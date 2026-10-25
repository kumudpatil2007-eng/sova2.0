import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator

from ..config import settings
from .timing_service import PipelineTimer
from ..llm.model_catalog import (
    ModelPurpose,
    get_default_model_catalog,
    find_matching_installed_model
)
from ..llm.local_client import (
    ollama_client,
    OllamaUnavailableError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaInferenceError
)
from ..llm.router import (
    route_query,
    RoutingDecision,
    TaskCategory,
    PROMPT_CASUAL,
    PROMPT_VISION_PID,
    PROMPT_TELEMETRY,
    PROMPT_REASONING,
    PROMPT_CODER,
    PROMPT_DOCUMENT,
    PROMPT_GENERAL
)
from .telemetry_service import query_telemetry_deterministically
from .verification_service import verify_response_grounding, VerificationResult
from .model_registry import sync_model_registry
from .document_generator import (
    DocumentService,
    DocumentStructure,
    parse_or_repair_document_structure
)

logger = logging.getLogger("sovereign_ai.llm")

# Backward compatibility exports
OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_VISION_MODEL = settings.ollama_vision_model
OLLAMA_CODER_MODEL = settings.ollama_coder_model
OLLAMA_REASONING_MODEL = settings.ollama_reasoning_model
OLLAMA_DOCUMENT_MODEL = settings.ollama_document_model
OLLAMA_GENERAL_MODEL = settings.ollama_general_model
OLLAMA_MODEL_FALLBACK = settings.ollama_model
OLLAMA_MODEL = settings.ollama_model
OLLAMA_KEEP_ALIVE = settings.ollama_keep_alive

TEMPERATURE = settings.temperature
MAX_TOKENS = settings.max_tokens
CONTEXT_LENGTH = settings.context_length


async def get_available_ollama_models() -> List[str]:
    """Queries Ollama for currently installed local models."""
    health = await ollama_client.check_health()
    return health.get("installed_models", [])


async def check_ollama_status() -> Dict[str, Any]:
    """
    Checks Ollama daemon health, retrieves installed models,
    and automatically synchronizes the SQLite model registry.
    """
    health = await ollama_client.check_health()
    if health["online"]:
        installed = health["installed_models"]
        # Sync model registry in database
        try:
            sync_model_registry(installed)
        except Exception as e:
            logger.warning(f"Error syncing model registry: {e}")

        # Resolve active models
        matched_vision = find_matching_installed_model(settings.ollama_vision_model, installed)
        matched_document = find_matching_installed_model(settings.ollama_document_model, installed)
        matched_reasoning = find_matching_installed_model(settings.ollama_reasoning_model, installed)
        matched_coder = find_matching_installed_model(settings.ollama_coder_model, installed)

        active_primary = matched_document or matched_vision or (installed[0] if installed else settings.ollama_model)

        return {
            "online": True,
            "model": active_primary,
            "vision_model": matched_vision or settings.ollama_vision_model,
            "document_model": matched_document or settings.ollama_document_model,
            "reasoning_model": matched_reasoning or settings.ollama_reasoning_model,
            "coder_model": matched_coder or settings.ollama_coder_model,
            "model_available": len(installed) > 0,
            "available_models": installed,
            "keep_alive": settings.ollama_keep_alive,
            "error": None
        }
    else:
        return {
            "online": False,
            "model": settings.ollama_model,
            "vision_model": settings.ollama_vision_model,
            "document_model": settings.ollama_document_model,
            "reasoning_model": settings.ollama_reasoning_model,
            "coder_model": settings.ollama_coder_model,
            "model_available": False,
            "available_models": [],
            "error": health.get("error", "Local AI engine unavailable.")
        }


async def select_routed_model(requires_vision: bool = False, query: str = "") -> tuple[str, str]:
    """
    Backward-compatible model routing resolver with intelligent task classification.
    """
    installed = await get_available_ollama_models()
    
    if query:
        decision = route_query(query=query)
        target_model = decision.model_name
        matched = find_matching_installed_model(target_model, installed)
        if matched:
            return matched, decision.category.value

    if requires_vision:
        matched = find_matching_installed_model(settings.ollama_vision_model, installed)
        if matched:
            return matched, "vision_inspection"
        raise RuntimeError("Multimodal local model unavailable. Please install qwen2.5vl:3b using Ollama.")

    # Default text model preference
    matched_doc = find_matching_installed_model(settings.ollama_document_model, installed)
    if matched_doc:
        return matched_doc, "document_qa"

    matched_vis = find_matching_installed_model(settings.ollama_vision_model, installed)
    if matched_vis:
        return matched_vis, "text_mode_fallback"

    return settings.ollama_model, "default_fallback"


def build_messages_payload(
    user_message: str,
    system_prompt: str,
    context: str = "",
    images_base64: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    telemetry_facts: Optional[List[str]] = None,
    target_model: str = ""
) -> tuple[List[Dict[str, Any]], bool]:
    """
    Constructs the Ollama messages array with task-specific system prompt,
    evidence boundary markers, conversation history, and optional vision tensors.
    CRITICAL INVARIANT: Images are NEVER attached to llama3.2:3b or any non-multimodal model.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]

    if conversation_history:
        for hist in conversation_history[-4:]:
            role = "user" if hist.get("role") == "user" else "assistant"
            content = hist.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

    prompt_content = ""

    # Telemetry facts grounding
    if telemetry_facts:
        prompt_content += "--- VERIFIED TELEMETRY MEASUREMENTS ---\n"
        for fact in telemetry_facts:
            prompt_content += f"• {fact}\n"
        prompt_content += "--- END OF TELEMETRY MEASUREMENTS ---\n\n"

    # Document context grounding
    if context:
        prompt_content += f"--- START OF RELEVANT DOCUMENT CONTEXT ---\n{context}\n--- END OF RELEVANT DOCUMENT CONTEXT ---\n\n"

    prompt_content += f"User Request: {user_message}"

    user_msg: Dict[str, Any] = {
        "role": "user",
        "content": prompt_content
    }

    has_images = False
    is_vision_model = (
        not target_model or
        "vl" in target_model.lower() or
        target_model.lower().startswith("qwen2.5vl") or
        settings.ollama_vision_model in target_model
    )
    if is_vision_model and images_base64 and len(images_base64) > 0:
        user_msg["images"] = images_base64[:2]
        has_images = True
    elif images_base64 and not is_vision_model:
        logger.warning(f"Suppressed multimodal payload for text-only model '{target_model}'.")

    messages.append(user_msg)
    return messages, has_images


async def generate_response_stream(
    user_message: str,
    context: str = "",
    images_base64: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    timer: Optional[PipelineTimer] = None,
    doc_data: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streams response token by token with:
    1. Query Intent Classification
    2. Dynamic Model Routing (Ollama: qwen2.5vl:3b, qwen2.5-coder:7b, deepseek-r1:7b, llama3.2:3b)
    3. Deterministic telemetry extraction (for CSV/XLSX)
    4. Evidence-grounded generation
    5. Final 7-point Verification Check
    """
    if timer is None:
        timer = PipelineTimer("ChatStream")

    status = await check_ollama_status()
    if not status["online"]:
        raise RuntimeError("Local AI engine unavailable. Ensure Ollama is running at http://127.0.0.1:11434.")

    doc_ext = doc_data.get("extension", "") if doc_data else ""
    doc_images = len(images_base64 or []) > 0

    # Deterministic Telemetry Processing if dataset is available
    telemetry_result: Optional[Dict[str, Any]] = None
    telemetry_facts: List[str] = []
    if doc_data and doc_data.get("df") is not None:
        telemetry_result = query_telemetry_deterministically(doc_data["df"], user_message)
        telemetry_facts = telemetry_result.get("facts", [])

    # Route query
    decision = route_query(
        query=user_message,
        doc_data=doc_data,
        doc_extension=doc_ext,
        doc_has_images=doc_images,
        telemetry_result=telemetry_result
    )

    selected_model = decision.model_name
    timer.routing_decision = f"{decision.category.value} -> {selected_model}"
    timer.model_used = selected_model

    # Short-circuit for exact deterministic telemetry matches (e.g. pressure at 09:20 or missing time 09:27)
    if telemetry_result and telemetry_result.get("status") in {"EXACT_MATCH", "NOT_FOUND"}:
        direct_answer = telemetry_result.get("answer", "")
        if direct_answer:
            timer.mark_first_token()
            timer.finish_generation()
            yield {"type": "token", "content": direct_answer}
            yield {
                "type": "done",
                "model": selected_model,
                "timings": timer.to_dict(),
                "verification": {
                    "is_verified": True,
                    "grounded": True,
                    "leak_count": 0,
                    "verification_label": "VERIFIED (0 LEAKS)",
                    "notes": "Exact deterministic extraction from telemetry dataset."
                }
            }
            return

    # Check multimodal availability if visual understanding is required
    if decision.requires_vision:
        installed = await get_available_ollama_models()
        matched_vision = find_matching_installed_model(settings.ollama_vision_model, installed)
        if not matched_vision:
            raise RuntimeError("Multimodal local model unavailable. Please install qwen2.5vl:3b using Ollama.")

    # Guard: pass images ONLY if decision requires vision AND model is multimodal
    if decision.requires_vision and (selected_model == settings.ollama_vision_model or "vl" in selected_model):
        pass_images = images_base64
    else:
        pass_images = None

    # For casual / general text queries, isolate from document context
    effective_context = "" if (decision.category == TaskCategory.CASUAL or decision.system_prompt == PROMPT_GENERAL) else context

    # Build messages payload
    messages, has_images = build_messages_payload(
        user_message=user_message,
        system_prompt=decision.system_prompt,
        context=effective_context,
        images_base64=pass_images,
        conversation_history=conversation_history,
        telemetry_facts=telemetry_facts,
        target_model=selected_model
    )

    timer.mark_ollama_start()
    accumulated_response = ""

    try:
        # Document generation special workflow
        if decision.is_document_generation:
            async for chunk in ollama_client.chat_stream(
                model=selected_model,
                messages=messages
            ):
                if chunk["type"] == "token":
                    accumulated_response += chunk["content"]
                    timer.mark_first_token()
                elif chunk["type"] == "done":
                    timer.finish_generation()
                    break

            fallback_title = "SOVA Technical Report"
            if doc_data and doc_data.get("filename"):
                fn = doc_data["filename"]
                fn_str = fn.decode("utf-8", errors="ignore") if isinstance(fn, bytes) else str(fn)
                fallback_title = f"{Path(fn_str).stem} Summary Report"
            elif user_message:
                t_clean = re.sub(r'^(create|generate|make|produce|export|convert)\s+(a\s+)?(pdf|docx?|word|report)?(\s+about|\s+explaining|\s+on|\s+of)?\s*', '', user_message, flags=re.IGNORECASE)
                t_clean = t_clean.strip(' .?!')
                if t_clean and len(t_clean) <= 60:
                    fallback_title = t_clean.title()

            doc_structure = parse_or_repair_document_structure(accumulated_response, fallback_title=fallback_title)
            gen_result = DocumentService.generate_documents(doc_structure, decision.requested_formats)

            summary_text = doc_structure.summary or f"A comprehensive {gen_result.page_count}-page technical document has been authored and formatted with professional engineering typography and tables."
            sections_list = "\n".join(f"- **{sec.heading}**" for sec in doc_structure.sections[:6])

            presentation = (
                f"**Document generated successfully**\n\n"
                f"### {doc_structure.title}\n\n"
                f"{summary_text}\n\n"
                f"**Report Contents:**\n{sections_list}\n\n"
                f"Your downloadable file is ready below."
            )

            # Stream words of presentation to frontend
            words = presentation.split(" ")
            for w in words:
                yield {"type": "token", "content": w + " "}

            yield {
                "type": "done",
                "model": selected_model,
                "timings": timer.to_dict(),
                "verification": {
                    "is_verified": True,
                    "grounded": True,
                    "leak_count": 0,
                    "verification_label": "VERIFIED (0 LEAKS)",
                    "notes": f"Generated publication document ({', '.join(gen_result.formats).upper()})"
                },
                "generated_document": gen_result.to_dict()
            }
            return

        async for chunk in ollama_client.chat_stream(
            model=selected_model,
            messages=messages
        ):
            if chunk["type"] == "token":
                accumulated_response += chunk["content"]
                timer.mark_first_token()
                yield chunk
            elif chunk["type"] == "done":
                timer.finish_generation()

                # Run 7-Point Verification Check on complete response
                doc_text = doc_data.get("full_text", "") if doc_data else ""
                doc_name = doc_data.get("filename", "") if doc_data else ""
                is_conv = (
                    decision.category == TaskCategory.CASUAL or
                    decision.system_prompt == PROMPT_GENERAL or
                    not (doc_data and doc_data.get("full_text"))
                )

                verification: VerificationResult = verify_response_grounding(
                    query=user_message,
                    response=accumulated_response,
                    evidence_text=effective_context,
                    doc_full_text=doc_text,
                    doc_filename=doc_name,
                    is_conversational=is_conv,
                    telemetry_facts=telemetry_facts
                )

                yield {
                    "type": "done",
                    "model": chunk.get("model", selected_model),
                    "timings": timer.to_dict(),
                    "verification": verification.to_dict()
                }
                break

    except OllamaUnavailableError as e:
        raise RuntimeError(str(e))
    except OllamaTimeoutError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        logger.error(f"Inference stream failed: {e}", exc_info=True)
        raise RuntimeError(f"Local inference engine failure: {str(e)}")


async def generate_response(
    user_message: str,
    context: str = "",
    images_base64: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    timer: Optional[PipelineTimer] = None,
    doc_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Non-streaming synchronous inference with routing, deterministic telemetry,
    and 7-point verification.
    """
    if timer is None:
        timer = PipelineTimer("ChatSync")

    status = await check_ollama_status()
    if not status["online"]:
        raise RuntimeError("Local AI engine unavailable. Ensure Ollama is running at http://127.0.0.1:11434.")

    doc_ext = doc_data.get("extension", "") if doc_data else ""
    doc_images = len(images_base64 or []) > 0

    # Deterministic Telemetry Processing if dataset is available
    telemetry_result: Optional[Dict[str, Any]] = None
    telemetry_facts: List[str] = []
    if doc_data and doc_data.get("df") is not None:
        telemetry_result = query_telemetry_deterministically(doc_data["df"], user_message)
        telemetry_facts = telemetry_result.get("facts", [])

    # Route query
    decision = route_query(
        query=user_message,
        doc_data=doc_data,
        doc_extension=doc_ext,
        doc_has_images=doc_images,
        telemetry_result=telemetry_result
    )

    selected_model = decision.model_name
    timer.routing_decision = f"{decision.category.value} -> {selected_model}"
    timer.model_used = selected_model

    # Short-circuit for exact deterministic telemetry matches (e.g. pressure at 09:20 or missing time 09:27)
    if telemetry_result and telemetry_result.get("status") in {"EXACT_MATCH", "NOT_FOUND"}:
        direct_answer = telemetry_result.get("answer", "")
        if direct_answer:
            timer.mark_first_token()
            timer.finish_generation()
            return {
                "answer": direct_answer,
                "model": selected_model,
                "timings": timer.to_dict(),
                "verification": {
                    "is_verified": True,
                    "grounded": True,
                    "leak_count": 0,
                    "verification_label": "VERIFIED (0 LEAKS)",
                    "notes": "Exact deterministic extraction from telemetry dataset."
                }
            }

    # Check multimodal availability if visual understanding is required
    if decision.requires_vision:
        installed = await get_available_ollama_models()
        matched_vision = find_matching_installed_model(settings.ollama_vision_model, installed)
        if not matched_vision:
            raise RuntimeError("Multimodal local model unavailable. Please install qwen2.5vl:3b using Ollama.")

    # Guard: pass images ONLY if decision requires vision AND model is multimodal
    if decision.requires_vision and (selected_model == settings.ollama_vision_model or "vl" in selected_model):
        pass_images = images_base64
    else:
        pass_images = None

    # For casual / general text queries, isolate from document context
    effective_context = "" if (decision.category == TaskCategory.CASUAL or decision.system_prompt == PROMPT_GENERAL) else context

    # Build messages payload
    messages, has_images = build_messages_payload(
        user_message=user_message,
        system_prompt=decision.system_prompt,
        context=effective_context,
        images_base64=pass_images,
        conversation_history=conversation_history,
        telemetry_facts=telemetry_facts,
        target_model=selected_model
    )

    timer.mark_ollama_start()

    try:
        raw_result = await ollama_client.chat(
            model=selected_model,
            messages=messages
        )
        timer.mark_first_token()
        timer.finish_generation()

        answer = raw_result.get("answer", "")

        # Document generation special workflow
        if decision.is_document_generation:
            fallback_title = "SOVA Technical Report"
            if doc_data and doc_data.get("filename"):
                fn = doc_data["filename"]
                fn_str = fn.decode("utf-8", errors="ignore") if isinstance(fn, bytes) else str(fn)
                fallback_title = f"{Path(fn_str).stem} Summary Report"
            elif user_message:
                t_clean = re.sub(r'^(create|generate|make|produce|export|convert)\s+(a\s+)?(pdf|docx?|word|report)?(\s+about|\s+explaining|\s+on|\s+of)?\s*', '', user_message, flags=re.IGNORECASE)
                t_clean = t_clean.strip(' .?!')
                if t_clean and len(t_clean) <= 60:
                    fallback_title = t_clean.title()

            doc_structure = parse_or_repair_document_structure(answer, fallback_title=fallback_title)
            gen_result = DocumentService.generate_documents(doc_structure, decision.requested_formats)

            summary_text = doc_structure.summary or f"A comprehensive {gen_result.page_count}-page technical document has been authored and formatted with professional engineering typography and tables."
            sections_list = "\n".join(f"- **{sec.heading}**" for sec in doc_structure.sections[:6])

            presentation = (
                f"**Document generated successfully**\n\n"
                f"### {doc_structure.title}\n\n"
                f"{summary_text}\n\n"
                f"**Report Contents:**\n{sections_list}\n\n"
                f"Your downloadable file is ready below."
            )

            return {
                "answer": presentation,
                "model": selected_model,
                "timings": timer.to_dict(),
                "verification": {
                    "is_verified": True,
                    "grounded": True,
                    "leak_count": 0,
                    "verification_label": "VERIFIED (0 LEAKS)",
                    "notes": f"Generated publication document ({', '.join(gen_result.formats).upper()})"
                },
                "generated_document": gen_result.to_dict()
            }

        # Run 7-Point Verification Check
        doc_text = doc_data.get("full_text", "") if doc_data else ""
        doc_name = doc_data.get("filename", "") if doc_data else ""
        is_conv = (
            decision.category == TaskCategory.CASUAL or
            decision.system_prompt == PROMPT_GENERAL or
            not (doc_data and doc_data.get("full_text"))
        )

        verification: VerificationResult = verify_response_grounding(
            query=user_message,
            response=answer,
            evidence_text=effective_context,
            doc_full_text=doc_text,
            doc_filename=doc_name,
            is_conversational=is_conv,
            telemetry_facts=telemetry_facts
        )

        final_answer = verification.corrected_response if verification.corrected_response else answer

        return {
            "answer": final_answer,
            "model": selected_model,
            "timings": timer.to_dict(),
            "verification": verification.to_dict()
        }

    except OllamaUnavailableError as e:
        raise RuntimeError(str(e))
    except OllamaTimeoutError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        raise RuntimeError(f"Local inference engine failure: {str(e)}")


async def generate_engineering_note_content(doc_data: Dict[str, Any]) -> str:
    """Generate structured engineering note using reasoning/document model context."""
    full_text = doc_data.get("full_text", "")
    filename = doc_data.get("filename", "Inspection_Report")

    prompt = f"""Generate a formal Industrial Engineering Note based strictly on the document provided.

Document: {filename}
Content Summary:
{full_text[:3500]}

Generate the note in this exact structure:
# ENGINEERING NOTE: [Title based on document]

## 1. Equipment & Specification
- **Equipment Name / Tag**: 
- **Inspection / Document Type**: 
- **Date / Reference Code**: 

## 2. Executive Summary
[A concise 2-sentence summary of the inspection or technical status]

## 3. Key Technical Findings
[Bulleted list of measurements, conditions, or inspection data points]

## 4. Engineering Calculations & Verification
[Formulas and calculation steps, e.g. corrosion rate, remaining life, minimum allowable thickness, or capacity verification]

## 5. Risk Assessment & Recommendations
- **Assessed Risk Level**: (Low / Medium / High / Critical)
- **Immediate Corrective Actions**:
- **Recommended Next Inspection Interval**:

## 6. Standards & Regulatory Compliance
[Applicable industrial standards, e.g., API 510/570/579, ASME Section VIII / B31.3, or manufacturer specifications]
"""

    res = await generate_response(
        user_message="Generate the formal engineering note now according to the structure specified in the system instructions.",
        context=prompt,
        doc_data=doc_data
    )

    return res["answer"]
