import os
from pathlib import Path
from typing import Dict, Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for resolving relative paths
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

ENV_FILE = ROOT_DIR / ".env" if (ROOT_DIR / ".env").exists() else BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    SOVA Centralized Configuration.
    Supports air-gapped local deployment, Ollama local model routing,
    and industrial verification parameters.
    """
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Local Ollama Daemon Configuration
    ollama_base_url: str = "http://127.0.0.1:11434"

    # Supported Open-Weight Models
    ollama_vision_model: str = "qwen2.5vl:3b"       # P&ID/image understanding & visual inspection
    ollama_coder_model: str = "qwen2.5-coder:7b"     # Code generation & data processing tasks
    ollama_reasoning_model: str = "deepseek-r1:7b"   # Multi-step reasoning & evidence synthesis
    ollama_document_model: str = "llama3.2:3b"      # General document Q&A & SOP retrieval
    ollama_general_model: str = "gemma2:9b"         # Optional general fallback model (non-mandatory)

    # Active default fallback model (text-only)
    ollama_model: str = "llama3.2:3b"

    # Keep-Alive: Optimized for 6GB VRAM (NVIDIA RTX 4050) to allow lazy loading/unloading
    ollama_keep_alive: str = "10m"

    # Generation Parameters
    temperature: float = 0.2
    max_tokens: int = 4096
    context_length: int = 4096

    # Backend Server
    host: str = "127.0.0.1"
    port: int = 8000
    max_file_size_mb: int = 50
    upload_dir: str = "uploads"

    # Strict Air-Gap & Hallucination Prevention Flags
    air_gapped: bool = True
    dev_mock_fallback: bool = False  # NEVER use mock/fabricated engineering data in production

    @property
    def model_mapping(self) -> Dict[str, str]:
        """Maps functional roles to model identifiers."""
        return {
            "vision": self.ollama_vision_model,
            "coder": self.ollama_coder_model,
            "reasoning": self.ollama_reasoning_model,
            "document": self.ollama_document_model,
            "general": self.ollama_general_model,
        }

    @property
    def required_models(self) -> List[str]:
        """List of models required for core functionality."""
        return [
            self.ollama_vision_model,
            self.ollama_coder_model,
            self.ollama_reasoning_model,
            self.ollama_document_model,
        ]


# Singleton settings instance
settings = Settings()
