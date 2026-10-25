import os
import uuid
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import UploadFile, HTTPException

UPLOAD_ROOT = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024  # 50 MB in bytes

ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".webp",
    ".csv", ".txt", ".docx", ".xlsx"
}

# In-memory file registry for session tracking
_file_registry: Dict[str, Dict[str, Any]] = {}


def ensure_upload_dir() -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT


def validate_file(filename: str, size: int):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB."
        )


async def save_uploaded_file(upload_file: UploadFile) -> Dict[str, Any]:
    ensure_upload_dir()
    filename = upload_file.filename or "uploaded_document"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    file_id = str(uuid.uuid4())
    session_dir = UPLOAD_ROOT / file_id
    session_dir.mkdir(parents=True, exist_ok=True)

    destination_path = session_dir / filename

    size = 0
    with open(destination_path, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                buffer.close()
                shutil.rmtree(session_dir, ignore_errors=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB."
                )
            buffer.write(chunk)

    record = {
        "file_id": file_id,
        "filename": filename,
        "file_path": str(destination_path),
        "extension": ext,
        "size": size,
        "mime_type": upload_file.content_type or "application/octet-stream",
        "status": "uploaded"
    }

    _file_registry[file_id] = record
    return record


def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    return _file_registry.get(file_id)


def register_file_record(file_id: str, record: Dict[str, Any]):
    _file_registry[file_id] = record


def list_files() -> list:
    return list(_file_registry.values())
