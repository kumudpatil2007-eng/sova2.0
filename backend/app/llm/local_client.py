import json
import time
import logging
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator

from ..config import settings
from .model_catalog import normalize_model_name, find_matching_installed_model

logger = logging.getLogger("sovereign_ai.ollama_client")


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaUnavailableError(OllamaClientError):
    """Raised when the local Ollama daemon cannot be reached."""
    pass


class OllamaModelNotFoundError(OllamaClientError):
    """Raised when a requested model is not installed in local Ollama."""
    pass


class OllamaTimeoutError(OllamaClientError):
    """Raised when Ollama inference times out."""
    pass


class OllamaInferenceError(OllamaClientError):
    """Raised when Ollama returns an error during inference."""
    pass


class OllamaLocalClient:
    """
    Robust, air-gapped local client for Ollama open-weight inference.
    Strictly local: 0 external API calls, 0 cloud egress.
    Features:
    - Health & model availability checks
    - Streaming & non-streaming chat completions
    - Time-to-first-token & generation telemetry
    - Lazy model loading & VRAM management (RTX 4050 6GB)
    - Zero fake/mock fallbacks on failure
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.keep_alive = settings.ollama_keep_alive
        self.default_options = {
            "temperature": settings.temperature,
            "top_p": 0.9,
            "num_predict": settings.max_tokens,
            "num_ctx": settings.context_length,
        }

    async def check_health(self, timeout: float = 3.0) -> Dict[str, Any]:
        """
        Queries Ollama daemon to check connectivity and retrieve installed models.
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return {
                        "online": True,
                        "installed_models": models,
                        "error": None
                    }
                return {
                    "online": False,
                    "installed_models": [],
                    "error": f"Ollama daemon returned HTTP {resp.status_code}"
                }
        except httpx.ConnectError:
            return {
                "online": False,
                "installed_models": [],
                "error": f"Cannot connect to local Ollama daemon at {self.base_url}. Ensure 'ollama serve' is running."
            }
        except httpx.TimeoutException:
            return {
                "online": False,
                "installed_models": [],
                "error": f"Connection to local Ollama daemon timed out after {timeout}s."
            }
        except Exception as e:
            return {
                "online": False,
                "installed_models": [],
                "error": str(e)
            }

    async def get_running_models(self, timeout: float = 3.0) -> List[Dict[str, Any]]:
        """Queries Ollama for currently loaded models in GPU/CPU VRAM."""
        url = f"{self.base_url}/api/ps"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json().get("models", [])
        except Exception as e:
            logger.debug(f"Could not query active models via /api/ps: {e}")
        return []

    async def resolve_available_model(self, requested_model: str) -> str:
        """
        Validates whether the requested model is installed in local Ollama.
        Returns the resolved installed model name, or raises an error.
        """
        health = await self.check_health()
        if not health["online"]:
            raise OllamaUnavailableError(
                f"Local model service unavailable. Could not connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running and no fake fallback is used."
            )

        installed = health["installed_models"]
        matched = find_matching_installed_model(requested_model, installed)
        if not matched:
            if requested_model == settings.ollama_vision_model or "vl" in requested_model.lower():
                raise OllamaModelNotFoundError(
                    "Multimodal local model unavailable. Please install qwen2.5vl:3b using Ollama."
                )
            raise OllamaModelNotFoundError(
                f"Requested local model '{requested_model}' is not installed in Ollama. "
                f"Installed models: {', '.join(installed) if installed else 'None'}. "
                f"Run: ollama pull {requested_model}"
            )
        return matched

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None,
        timeout: float = 180.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams response tokens asynchronously from local Ollama.
        Yields:
          {"type": "token", "content": "..."}
          {"type": "done", "model": "...", "timings": {...}}
        """
        resolved_model = await self.resolve_available_model(model)
        merged_options = {**self.default_options, **(options or {})}

        # Invariant safety net: NEVER send multimodal image payloads to text-only models
        is_multimodal = ("vl" in resolved_model.lower() or "vision" in resolved_model.lower())
        if not is_multimodal:
            sanitized_messages = []
            for msg in messages:
                if "images" in msg:
                    cleaned_msg = dict(msg)
                    cleaned_msg.pop("images", None)
                    sanitized_messages.append(cleaned_msg)
                else:
                    sanitized_messages.append(msg)
            messages = sanitized_messages

        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
            "keep_alive": keep_alive or self.keep_alive,
            "options": merged_options
        }

        url = f"{self.base_url}/api/chat"
        t_start = time.perf_counter()
        t_first_token: Optional[float] = None

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        err_text = body.decode("utf-8", errors="ignore")
                        raise OllamaInferenceError(
                            f"Ollama inference error HTTP {response.status_code}: {err_text}"
                        )

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            if t_first_token is None:
                                t_first_token = time.perf_counter() - t_start
                            yield {
                                "type": "token",
                                "content": content
                            }

                        if chunk.get("done", False):
                            t_total = time.perf_counter() - t_start
                            yield {
                                "type": "done",
                                "model": resolved_model,
                                "timings": {
                                    "time_to_first_token_s": round(t_first_token or 0.0, 3),
                                    "total_generation_s": round(t_total, 3),
                                    "eval_count": chunk.get("eval_count", 0),
                                    "eval_duration_ms": round(chunk.get("eval_duration", 0) / 1e6, 1)
                                }
                            }
                            break

        except httpx.ConnectError:
            raise OllamaUnavailableError(
                f"Connection to local Ollama daemon failed at {self.base_url}. Ensure 'ollama serve' is active."
            )
        except httpx.TimeoutException:
            raise OllamaTimeoutError(
                f"Inference with model '{resolved_model}' timed out after {timeout}s."
            )

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Non-streaming chat completion from local Ollama.
        """
        resolved_model = await self.resolve_available_model(model)
        merged_options = {**self.default_options, **(options or {})}

        # Invariant safety net: NEVER send multimodal image payloads to text-only models
        is_multimodal = ("vl" in resolved_model.lower() or "vision" in resolved_model.lower())
        if not is_multimodal:
            sanitized_messages = []
            for msg in messages:
                if "images" in msg:
                    cleaned_msg = dict(msg)
                    cleaned_msg.pop("images", None)
                    sanitized_messages.append(cleaned_msg)
                else:
                    sanitized_messages.append(msg)
            messages = sanitized_messages

        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "keep_alive": keep_alive or self.keep_alive,
            "options": merged_options
        }

        url = f"{self.base_url}/api/chat"
        t_start = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise OllamaInferenceError(
                        f"Ollama returned error {resp.status_code}: {resp.text}"
                    )

                data = resp.json()
                t_total = time.perf_counter() - t_start

                content = data.get("message", {}).get("content", "").strip()
                if not content:
                    content = data.get("response", "").strip()

                return {
                    "answer": content,
                    "model": resolved_model,
                    "timings": {
                        "total_generation_s": round(t_total, 3),
                        "eval_count": data.get("eval_count", 0),
                    }
                }

        except httpx.ConnectError:
            raise OllamaUnavailableError(
                f"Local model service unavailable. Cannot connect to Ollama at {self.base_url}."
            )
        except httpx.TimeoutException:
            raise OllamaTimeoutError(
                f"Local model '{resolved_model}' timed out after {timeout}s."
            )


# Singleton client instance
ollama_client = OllamaLocalClient()
