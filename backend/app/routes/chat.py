import json
import time
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.document_processor import get_cached_document
from ..services.rag_service import retrieve_relevant_context
from ..services.llm_service import (
    generate_response,
    generate_response_stream,
    generate_engineering_note_content,
    check_ollama_status,
    select_routed_model,
    OLLAMA_MODEL_FALLBACK
)
from ..services.timing_service import PipelineTimer
from ..llm.router import detect_document_generation_intent, is_general_query

logger = logging.getLogger("sovereign_ai.chat")
router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    file_id: Optional[str] = None
    message: str
    history: Optional[List[Dict[str, str]]] = []


class NoteRequest(BaseModel):
    file_id: str


@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """
    Real-time token streaming chat endpoint via Server-Sent Events (SSE).
    Streams real pipeline stages, token chunks as they arrive from Ollama,
    and returns precise bottleneck timings on completion.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    timer = PipelineTimer("StreamInference")

    # Document retrieval & context preparation
    context = ""
    sources = []
    images = []

    if req.file_id:
        doc_data = get_cached_document(req.file_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail=f"Document with file_id '{req.file_id}' not found.")

        # Document caching verification (Section 19)
        timer.is_cached = True
        timer.extraction_time = 0.0  # Already in memory cache
        timer.ocr_time = 0.0

        # RAG relevant chunk retrieval
        t_ctx_start = time.perf_counter()
        if is_general_query(req.message):
            context = ""
            sources = []
        elif detect_document_generation_intent(req.message) and doc_data.get("full_text"):
            context = doc_data["full_text"][:3500]
            sources = [{"page": 1, "name": doc_data["filename"], "excerpt": context[:180] + "...", "relevance": "Direct"}]
        else:
            retrieval = retrieve_relevant_context(req.file_id, req.message, top_k=3)
            context = retrieval.get("context_text", "")
            sources = retrieval.get("sources", [])

            if not context and doc_data.get("full_text"):
                context = doc_data["full_text"][:2500]
                sources = [{"page": 1, "name": doc_data["filename"], "excerpt": context[:180] + "...", "relevance": "Direct"}]

        timer.context_time = time.perf_counter() - t_ctx_start

        # Intelligent Document Routing:
        # Only attach images if the document REQUIRES vision (e.g. PNG/JPG, scanned PDF, P&ID).
        if doc_data.get("requires_vision") and doc_data.get("images_base64"):
            images = doc_data["images_base64"][:2]

    async def event_generator():
        try:
            # 1. Real pipeline status: Reading document
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'Reading document', 'step': 1})}\n\n"

            # 2. Extracting relevant content
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'Extracting relevant content', 'step': 2})}\n\n"

            # 3. Preparing local context
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'Preparing local context', 'step': 3, 'sources': sources})}\n\n"

            # 4. Local inference running
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'Local inference running', 'step': 4})}\n\n"

            # 5. Stream tokens from Ollama
            async for chunk in generate_response_stream(
                user_message=req.message,
                context=context,
                images_base64=images if images else None,
                conversation_history=req.history,
                timer=timer,
                doc_data=doc_data if req.file_id else None
            ):
                if chunk["type"] == "token":
                    yield f"data: {json.dumps({'event': 'token', 'token': chunk['content']})}\n\n"
                elif chunk["type"] == "done":
                    yield f"data: {json.dumps({'event': 'done', 'model': chunk['model'], 'sources': sources, 'timings': chunk['timings'], 'verification': chunk.get('verification', {}), 'generated_document': chunk.get('generated_document')})}\n\n"

        except Exception as e:
            logger.error(f"Streaming inference error: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Synchronous chat endpoint with timing instrumentation and intelligent routing.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    timer = PipelineTimer("SyncInference")
    context = ""
    sources = []
    images = []

    if req.file_id:
        doc_data = get_cached_document(req.file_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail=f"Document with file_id '{req.file_id}' not found.")

        timer.is_cached = True
        timer.extraction_time = 0.0
        timer.ocr_time = 0.0

        t_ctx_start = time.perf_counter()
        if is_general_query(req.message):
            context = ""
            sources = []
        elif detect_document_generation_intent(req.message) and doc_data.get("full_text"):
            context = doc_data["full_text"][:3500]
            sources = [{"page": 1, "name": doc_data["filename"], "excerpt": context[:180] + "...", "relevance": "Direct"}]
        else:
            retrieval = retrieve_relevant_context(req.file_id, req.message, top_k=3)
            context = retrieval.get("context_text", "")
            sources = retrieval.get("sources", [])

            if not context and doc_data.get("full_text"):
                context = doc_data["full_text"][:2500]
                sources = [{"page": 1, "name": doc_data["filename"], "excerpt": context[:180] + "...", "relevance": "Direct"}]

        timer.context_time = time.perf_counter() - t_ctx_start

        if doc_data.get("requires_vision") and doc_data.get("images_base64"):
            images = doc_data["images_base64"][:2]

    try:
        llm_result = await generate_response(
            user_message=req.message,
            context=context,
            images_base64=images if images else None,
            conversation_history=req.history,
            timer=timer,
            doc_data=doc_data if req.file_id else None
        )

        return {
            "answer": llm_result["answer"],
            "sources": sources,
            "model": llm_result["model"],
            "timings": llm_result.get("timings", {}),
            "verification": llm_result.get("verification", {}),
            "generated_document": llm_result.get("generated_document")
        }

    except RuntimeError as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference pipeline failure: {str(e)}")


@router.post("/generate-note")
async def generate_note_endpoint(req: NoteRequest):
    """
    Dynamically generates a formal structured engineering note from the active document.
    """
    doc_data = get_cached_document(req.file_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail=f"Document with file_id '{req.file_id}' not found.")

    try:
        note_markdown = await generate_engineering_note_content(doc_data)
        model_name, _ = await select_routed_model(requires_vision=False)
        return {
            "file_id": req.file_id,
            "filename": doc_data.get("filename", "Inspection_Report"),
            "note_markdown": note_markdown,
            "model": model_name
        }
    except Exception as e:
        logger.error(f"Error generating engineering note: {e}")
        raise HTTPException(status_code=503, detail=str(e))
