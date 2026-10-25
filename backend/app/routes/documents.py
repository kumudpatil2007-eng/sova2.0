import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..services.document_processor import get_cached_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

SAMPLE_PDF_PATH = Path("sample_data/Heat_Exchanger_E204_Inspection_Report.pdf").resolve()


@router.get("/sample")
async def get_sample_document():
    """
    Returns the real sample inspection PDF so the user/judge can test
    the entire real pipeline with a single click.
    """
    if not SAMPLE_PDF_PATH.exists():
        # Check relative to backend directory
        alt_path = Path(__file__).resolve().parent.parent.parent / "sample_data" / "Heat_Exchanger_E204_Inspection_Report.pdf"
        if alt_path.exists():
            return FileResponse(
                path=str(alt_path),
                filename="Heat_Exchanger_E204_Inspection_Report.pdf",
                media_type="application/pdf"
            )
        raise HTTPException(status_code=404, detail="Sample inspection document not found.")

    return FileResponse(
        path=str(SAMPLE_PDF_PATH),
        filename="Heat_Exchanger_E204_Inspection_Report.pdf",
        media_type="application/pdf"
    )


@router.get("/{file_id}")
async def get_document_details(file_id: str):
    """Returns extracted document structure and metadata by file_id."""
    doc = get_cached_document(file_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "file_id": doc["file_id"],
        "filename": doc["filename"],
        "total_pages": doc.get("total_pages", 1),
        "extension": doc.get("extension", ""),
        "metadata": doc.get("metadata", {}),
        "page_summaries": [
            {"page_number": p["page_number"], "char_count": p.get("char_count", 0)}
            for p in doc.get("pages", [])
        ]
    }


# --- GENERATED DOCUMENT ENDPOINTS ---

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..services.document_generator import (
    DocumentService,
    DocumentStructure,
    parse_or_repair_document_structure
)
from ..services.llm_service import generate_response


class GenerateDocumentRequest(BaseModel):
    prompt: Optional[str] = None
    file_id: Optional[str] = None
    title: Optional[str] = None
    formats: Optional[List[str]] = ["pdf", "docx"]
    structure: Optional[Dict[str, Any]] = None


@router.post("/generate")
async def generate_document_endpoint(req: GenerateDocumentRequest):
    """
    Direct endpoint to generate a professional PDF and/or DOCX document.
    Can accept either a pre-structured document payload OR an instruction prompt.
    """
    formats = req.formats or ["pdf", "docx"]

    # 1. Direct structured payload provided
    if req.structure:
        try:
            doc_struct = DocumentStructure(**req.structure)
            result = DocumentService.generate_documents(doc_struct, formats)
            return result.to_dict()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid document structure: {str(e)}")

    # 2. Prompt provided: run through LLM to author structured content
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Either 'structure' or 'prompt' must be provided.")

    try:
        doc_data = None
        context = ""
        if req.file_id:
            doc_data = get_cached_document(req.file_id)
            if doc_data:
                context = doc_data.get("full_text", "")[:3500]

        llm_res = await generate_response(
            user_message=req.prompt,
            context=context,
            doc_data=doc_data
        )

        gen_doc = llm_res.get("generated_document")
        if gen_doc:
            return gen_doc

        # If LLM generated answer without doc_gen trigger, force parse it
        fallback_title = req.title or "SOVA Generated Report"
        doc_struct = parse_or_repair_document_structure(llm_res.get("answer", ""), fallback_title=fallback_title)
        result = DocumentService.generate_documents(doc_struct, formats)
        return result.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")


@router.get("/generated/{doc_id}")
async def get_generated_document_metadata(doc_id: str):
    """Returns metadata for a previously generated document."""
    meta = DocumentService.get_generated_document(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Generated document not found.")
    return meta


@router.get("/generated/{doc_id}/download")
async def download_generated_document(doc_id: str, format: str = "pdf"):
    """
    Downloads a generated document file (PDF or DOCX) with proper headers.
    Completely isolates internal file paths from the client.
    """
    file_info = DocumentService.get_file_for_download(doc_id, format)
    if not file_info:
        raise HTTPException(
            status_code=404,
            detail=f"Requested document '{doc_id}' in format '{format}' not found."
        )

    local_path, filename, media_type = file_info
    return FileResponse(
        path=local_path,
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
