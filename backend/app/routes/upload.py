import time
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.file_service import save_uploaded_file
from ..services.document_processor import process_document
from ..services.rag_service import chunk_document

logger = logging.getLogger("sovereign_ai.upload")
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Real local file upload endpoint. Receives actual multipart/form-data,
    stores the file in local workspace directory, extracts content locally,
    and indexes chunks for RAG.
    """
    t0 = time.perf_counter()
    try:
        # 1. Save uploaded file to local workspace directory
        file_record = await save_uploaded_file(file)
        t_save = time.perf_counter() - t0
        file_id = file_record["file_id"]
        file_path = file_record["file_path"]
        filename = file_record["filename"]

        # 2. Extract content locally (PyMuPDF / OCR / Pandas)
        t_proc_start = time.perf_counter()
        doc_data = await process_document(file_path, filename, file_id)
        t_proc = time.perf_counter() - t_proc_start

        # 3. Chunk text and index locally
        t_chunk_start = time.perf_counter()
        chunk_document(doc_data)
        t_chunk = time.perf_counter() - t_chunk_start

        t_total = time.perf_counter() - t0

        logger.info(
            f"[Upload Pipeline] File: '{filename}' | Save: {t_save:.2f}s | "
            f"Extraction: {t_proc:.2f}s | Chunking: {t_chunk:.2f}s | Total: {t_total:.2f}s"
        )
        print(f"[Document] upload & save: {t_save:.2f}s")
        print(f"[Document] extraction: {t_proc:.2f}s")
        print(f"[Context] chunk indexing: {t_chunk:.2f}s")

        return {
            "file_id": file_id,
            "filename": filename,
            "mime_type": file_record["mime_type"],
            "size": file_record["size"],
            "total_pages": doc_data.get("total_pages", 1),
            "status": "uploaded",
            "has_images": len(doc_data.get("images_base64", [])) > 0,
            "timings": {
                "save_s": round(t_save, 2),
                "extraction_s": round(t_proc, 2),
                "chunking_s": round(t_chunk, 2),
                "total_s": round(t_total, 2)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
