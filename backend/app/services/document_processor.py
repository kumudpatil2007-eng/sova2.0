import io
import time
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

from .ocr_service import run_ocr

logger = logging.getLogger("sovereign_ai.doc_processor")

# In-memory cache of processed documents keyed by file_id
_document_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_document(file_id: str) -> Optional[Dict[str, Any]]:
    return _document_cache.get(file_id)


def cache_document(file_id: str, doc_data: Dict[str, Any]):
    _document_cache[file_id] = doc_data


def resize_image_for_vram(img: Image.Image, max_dim: int = 1536) -> Image.Image:
    """
    Optimizes image dimensions for 4GB VRAM GPU (RTX 3050).
    Preserves aspect ratio and text readability while preventing VRAM exhaustion.
    """
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return img


async def process_document(file_path: str, filename: str, file_id: str) -> Dict[str, Any]:
    """
    Processes a document with intelligent routing:
    - Text PDFs: Fast native extraction via PyMuPDF (0 rendering, pure text context)
    - Scanned PDFs: Local OCR only where text is absent
    - Images: Optimized resize & encode for vision model
    - Caches results to prevent redundant processing on follow-up questions
    """
    # Check cache first
    existing = get_cached_document(file_id)
    if existing:
        logger.info(f"Reusing cached document data for file_id: {file_id}")
        return existing

    path = Path(file_path)
    ext = path.suffix.lower()
    logger.info(f"Processing new document '{filename}' ({ext}) [file_id: {file_id}]")

    doc_data: Dict[str, Any] = {
        "file_id": file_id,
        "filename": filename,
        "extension": ext,
        "total_pages": 1,
        "pages": [],
        "full_text": "",
        "images_base64": [],
        "requires_vision": False,
        "is_scanned": False,
        "metadata": {},
        "timings": {
            "extraction_s": 0.0,
            "ocr_s": 0.0,
            "image_render_s": 0.0
        }
    }

    try:
        if ext == ".pdf":
            doc_data = await _process_pdf(path, filename, file_id)
        elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
            doc_data = await _process_image(path, filename, file_id)
        elif ext == ".csv":
            doc_data = await _process_csv(path, filename, file_id)
        elif ext == ".txt":
            doc_data = await _process_txt(path, filename, file_id)
        elif ext in {".docx", ".doc"}:
            doc_data = await _process_docx(path, filename, file_id)
        elif ext in {".xlsx", ".xls"}:
            doc_data = await _process_xlsx(path, filename, file_id)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    except Exception as e:
        logger.error(f"Error processing {filename}: {e}", exc_info=True)
        doc_data["error"] = str(e)
        if not doc_data["full_text"]:
            doc_data["full_text"] = f"[Error reading document: {e}]"

    cache_document(file_id, doc_data)
    return doc_data


async def _process_pdf(path: Path, filename: str, file_id: str) -> Dict[str, Any]:
    """
    Intelligent PDF processing:
    1. Extracts text natively via PyMuPDF.
    2. If text is present, treats as normal text PDF (NO page image rendering).
    3. If text is missing/scanned, runs local OCR.
    """
    import pymupdf as fitz

    t0 = time.perf_counter()
    doc = fitz.open(str(path))
    total_pages = len(doc)
    pages: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []
    images_base64: List[str] = []

    # First pass: native text extraction
    total_native_chars = 0
    raw_pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        raw_pages_text.append(text)
        total_native_chars += len(text)

    extraction_time = time.perf_counter() - t0
    ocr_time = 0.0
    image_render_time = 0.0

    avg_chars_per_page = total_native_chars / max(1, total_pages)
    total_raster_images = sum(len(p.get_images()) for p in doc)
    is_scanned = (avg_chars_per_page < 40 and total_pages > 0)

    # Check if this document represents a P&ID, flow diagram, or technical drawing
    is_pid_drawing = any(k in filename.lower() for k in ["pid", "p_and_id", "p&id", "drawing", "flow", "schematic", "diagram"])
    if not is_pid_drawing and total_pages <= 5:
        # Check if pages have complex vector drawings (e.g. >35 paths; simple tables have <20)
        try:
            if any(len(p.get_drawings()) > 35 for p in doc):
                is_pid_drawing = True
        except Exception:
            pass

    # Visual understanding is required if the PDF is scanned, a P&ID/drawing, or image-heavy
    requires_vision = bool(is_scanned or is_pid_drawing or (total_raster_images > 0 and avg_chars_per_page < 100))

    if requires_vision:
        # Render page 1 (and 2 if exists) to base64 for visual model (qwen2.5vl:3b)
        logger.info(f"PDF '{filename}' requires visual understanding (scanned={is_scanned}, pid={is_pid_drawing}, imgs={total_raster_images}). Rendering visual frames...")
        t_rend_start = time.perf_counter()
        for p_idx in range(min(2, total_pages)):
            pix = doc[p_idx].get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            pil_img = resize_image_for_vram(pil_img, max_dim=1536)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=85)
            images_base64.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
        image_render_time = time.perf_counter() - t_rend_start
    else:
        requires_vision = False

    if not is_scanned:
        # NORMAL TEXT PDF:
        for i, text in enumerate(raw_pages_text):
            page_num = i + 1
            pages.append({
                "page_number": page_num,
                "text": text,
                "char_count": len(text)
            })
            if text:
                full_text_parts.append(f"--- [Page {page_num}] ---\n{text}")

        logger.info(f"PDF '{filename}' processed ({total_native_chars} chars across {total_pages} pages, vision={requires_vision})")

    else:
        # SCANNED PDF:
        # Fallback to OCR for pages lacking native text
        logger.info(f"PDF '{filename}' detected as SCANNED (avg {avg_chars_per_page:.1f} chars/page). Running local OCR...")
        t_ocr_start = time.perf_counter()

        for i, page in enumerate(doc):
            page_num = i + 1
            page_text = raw_pages_text[i]

            if len(page_text) < 40:
                # Render page to pixmap for local OCR
                t_rend = time.perf_counter()
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                image_render_time += (time.perf_counter() - t_rend)

                pil_img = Image.open(io.BytesIO(img_bytes))
                ocr_text = run_ocr(pil_img)
                if ocr_text:
                    page_text = f"[Scanned Page {page_num} OCR]:\n{ocr_text}"

            pages.append({
                "page_number": page_num,
                "text": page_text,
                "char_count": len(page_text)
            })
            if page_text:
                full_text_parts.append(f"--- [Page {page_num}] ---\n{page_text}")

        ocr_time = time.perf_counter() - t_ocr_start

    doc.close()
    full_text = "\n\n".join(full_text_parts) if full_text_parts else "[No text could be extracted from this PDF]"

    return {
        "file_id": file_id,
        "filename": filename,
        "extension": ".pdf",
        "total_pages": total_pages,
        "pages": pages,
        "full_text": full_text,
        "images_base64": images_base64,
        "requires_vision": requires_vision,
        "is_scanned": is_scanned,
        "metadata": {
            "page_count": total_pages,
            "char_count": len(full_text),
            "is_scanned": is_scanned
        },
        "timings": {
            "extraction_s": extraction_time,
            "ocr_s": ocr_time,
            "image_render_s": image_render_time
        }
    }


async def _process_image(path: Path, filename: str, file_id: str) -> Dict[str, Any]:
    """
    Image processing with resolution optimization for 4GB VRAM GPU.
    """
    t_start = time.perf_counter()
    with Image.open(path) as raw_img:
        rgb_img = raw_img.convert("RGB")
        # Resize if oversized (saves massive VRAM without losing technical text clarity)
        rgb_img = resize_image_for_vram(rgb_img, max_dim=1536)

        buffered = io.BytesIO()
        rgb_img.save(buffered, format="JPEG", quality=85)
        img_bytes = buffered.getvalue()
        b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Run local OCR to assist context
        ocr_text = run_ocr(rgb_img)

    proc_time = time.perf_counter() - t_start

    text = f"[Image Document: {filename}]\n"
    if ocr_text:
        text += f"Extracted Text:\n{ocr_text}"
    else:
        text += "Image document ready for multimodal visual inspection."

    return {
        "file_id": file_id,
        "filename": filename,
        "extension": path.suffix.lower(),
        "total_pages": 1,
        "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
        "full_text": text,
        "images_base64": [b64],
        "requires_vision": True,
        "is_scanned": False,
        "metadata": {
            "width": rgb_img.width,
            "height": rgb_img.height,
            "format": path.suffix.lower()
        },
        "timings": {
            "extraction_s": 0.0,
            "ocr_s": proc_time,
            "image_render_s": proc_time
        }
    }


async def _process_csv(path: Path, filename: str, file_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    import pandas as pd
    df = pd.read_csv(str(path))
    rows, cols = df.shape
    summary_lines = [
        f"Engineering Dataset: {filename}",
        f"Dimensions: {rows} rows x {cols} columns",
        f"Columns: {', '.join(df.columns.astype(str))}",
        "\nData Preview (first 10 rows):",
        df.head(10).to_markdown(index=False) if hasattr(df.head(10), "to_markdown") else df.head(10).to_string()
    ]
    numeric_df = df.select_dtypes(include=["number"])
    if not numeric_df.empty:
        summary_lines.append("\nStatistical Summary (Key Metrics):")
        summary_lines.append(numeric_df.describe().to_string())

    full_text = "\n".join(summary_lines)
    return {
        "file_id": file_id,
        "filename": filename,
        "extension": ".csv",
        "file_path": str(path),
        "df": df,
        "total_pages": 1,
        "pages": [{"page_number": 1, "text": full_text, "char_count": len(full_text)}],
        "full_text": full_text,
        "images_base64": [],
        "requires_vision": False,
        "is_scanned": False,
        "metadata": {"rows": rows, "columns": cols},
        "timings": {"extraction_s": time.perf_counter() - t0, "ocr_s": 0.0, "image_render_s": 0.0}
    }


async def _process_txt(path: Path, filename: str, file_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    return {
        "file_id": file_id,
        "filename": filename,
        "extension": ".txt",
        "total_pages": 1,
        "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
        "full_text": text,
        "images_base64": [],
        "requires_vision": False,
        "is_scanned": False,
        "metadata": {"char_count": len(text)},
        "timings": {"extraction_s": time.perf_counter() - t0, "ocr_s": 0.0, "image_render_s": 0.0}
    }


async def _process_docx(path: Path, filename: str, file_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        import docx
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        table_data = []
        for table in doc.tables:
            for row in table.rows:
                table_data.append(" | ".join([cell.text.strip() for cell in row.cells]))
        full_text = "\n".join(paragraphs)
        if table_data:
            full_text += "\n\nTables:\n" + "\n".join(table_data)
    except Exception as e:
        full_text = f"[Error reading DOCX: {e}]"

    return {
        "file_id": file_id,
        "filename": filename,
        "extension": ".docx",
        "total_pages": 1,
        "pages": [{"page_number": 1, "text": full_text, "char_count": len(full_text)}],
        "full_text": full_text,
        "images_base64": [],
        "requires_vision": False,
        "is_scanned": False,
        "metadata": {"char_count": len(full_text)},
        "timings": {"extraction_s": time.perf_counter() - t0, "ocr_s": 0.0, "image_render_s": 0.0}
    }


async def _process_xlsx(path: Path, filename: str, file_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    import pandas as pd
    excel_file = pd.ExcelFile(str(path))
    sheet_summaries = []
    first_df = None
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        if first_df is None:
            first_df = df
        sheet_summaries.append(f"--- Sheet: {sheet_name} ({df.shape[0]} rows x {df.shape[1]} cols) ---")
        sheet_summaries.append(df.head(10).to_string())
    full_text = "\n\n".join(sheet_summaries)
    return {
        "file_id": file_id,
        "filename": filename,
        "extension": ".xlsx",
        "file_path": str(path),
        "df": first_df,
        "total_pages": len(excel_file.sheet_names),
        "pages": [{"page_number": 1, "text": full_text, "char_count": len(full_text)}],
        "full_text": full_text,
        "images_base64": [],
        "requires_vision": False,
        "is_scanned": False,
        "metadata": {"sheets": excel_file.sheet_names},
        "timings": {"extraction_s": time.perf_counter() - t0, "ocr_s": 0.0, "image_render_s": 0.0}
    }
