import os
import re
import json
import uuid
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pymupdf

from .models import DocumentStructure, DocumentSection, DocumentTable, DocumentCodeBlock
from .docx_generator import generate_docx
from .pdf_generator import generate_pdf

logger = logging.getLogger("sovereign_ai.document_generator")

# Safe local storage directory for generated documents
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_DOCS_DIR = BASE_DIR / "data" / "generated_docs"
GENERATED_DOCS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory registry cache
_DOCUMENT_REGISTRY: Dict[str, Dict[str, Any]] = {}


def format_bytes(size: int) -> str:
    """Formats byte counts into human-readable strings."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def sanitize_filename(name: str) -> str:
    """Sanitizes document title into a filesystem-safe base name."""
    clean = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    clean = re.sub(r'\s+', '_', clean.strip())
    return clean[:60] or "SOVA_Document"


def parse_markdown_to_structure(text: str, fallback_title: str = "SOVA Technical Report") -> DocumentStructure:
    """
    Robust Markdown-to-DocumentStructure parser.
    Converts unstructured Markdown into a high-fidelity DocumentStructure model.
    """
    lines = text.strip().split('\n')
    title = fallback_title
    subtitle = None
    summary = None
    sections: List[DocumentSection] = []
    
    current_sec: Optional[DocumentSection] = None
    current_table_headers: List[str] = []
    current_table_rows: List[List[str]] = []
    in_code_block = False
    code_lang = "text"
    code_lines: List[str] = []

    def flush_table():
        nonlocal current_table_headers, current_table_rows, current_sec
        if current_table_headers or current_table_rows:
            if current_sec is None:
                current_sec = DocumentSection(heading="Overview", level=1)
                sections.append(current_sec)
            current_sec.tables.append(DocumentTable(
                headers=current_table_headers,
                rows=current_table_rows
            ))
            current_table_headers = []
            current_table_rows = []

    def flush_code():
        nonlocal in_code_block, code_lang, code_lines, current_sec
        if code_lines:
            if current_sec is None:
                current_sec = DocumentSection(heading="Code / Calculations", level=1)
                sections.append(current_sec)
            current_sec.code_blocks.append(DocumentCodeBlock(
                language=code_lang,
                code='\n'.join(code_lines)
            ))
            code_lines = []
            in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Code block handling
        if stripped.startswith('```'):
            if in_code_block:
                flush_code()
            else:
                flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip() or "text"
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Table row handling
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            # Check if separator row (e.g. |---|---|)
            if all(re.match(r'^-+$', c) for c in cells):
                continue
            if not current_table_headers:
                current_table_headers = cells
            else:
                current_table_rows.append(cells)
            continue
        else:
            flush_table()

        # Empty lines
        if not stripped:
            continue

        # Document Title (# Title)
        if stripped.startswith('# ') and title == fallback_title:
            title = stripped[2:].strip()
            continue

        # Headings (## Section, ### Subsection)
        if stripped.startswith('## '):
            heading_text = stripped[3:].strip()
            current_sec = DocumentSection(heading=heading_text, level=1)
            sections.append(current_sec)
            continue
        elif stripped.startswith('### '):
            heading_text = stripped[4:].strip()
            current_sec = DocumentSection(heading=heading_text, level=2)
            sections.append(current_sec)
            continue
        elif stripped.startswith('#### '):
            heading_text = stripped[5:].strip()
            current_sec = DocumentSection(heading=heading_text, level=3)
            sections.append(current_sec)
            continue

        # Bullet points
        if stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('• '):
            bullet_text = stripped[2:].strip()
            if current_sec is None:
                current_sec = DocumentSection(heading="Key Information", level=1)
                sections.append(current_sec)
            current_sec.bullet_points.append(bullet_text)
            continue

        # Numbered items
        num_match = re.match(r'^\d+[\.\)]\s+(.+)', stripped)
        if num_match:
            item_text = num_match.group(1).strip()
            if current_sec is None:
                current_sec = DocumentSection(heading="Procedures & Steps", level=1)
                sections.append(current_sec)
            current_sec.numbered_list.append(f"{len(current_sec.numbered_list) + 1}. {item_text}")
            continue

        # Regular Paragraph
        if current_sec is None:
            # Could be summary or intro paragraph
            if not summary:
                summary = stripped
            else:
                current_sec = DocumentSection(heading="Introduction", level=1)
                sections.append(current_sec)
                current_sec.paragraphs.append(stripped)
        else:
            current_sec.paragraphs.append(stripped)

    flush_table()
    flush_code()

    if not sections:
        sections.append(DocumentSection(
            heading="Document Content",
            level=1,
            paragraphs=[text[:3000]]
        ))

    return DocumentStructure(
        title=title,
        subtitle=subtitle,
        summary=summary,
        sections=sections
    )


def repair_truncated_json(s: str) -> str:
    """Balances quotes, trailing commas, and brackets in truncated JSON strings."""
    start = s.find('{')
    if start == -1:
        return s
    s = s[start:].rstrip('` \r\n')

    # If it ends inside a string literal, balance quotes
    quotes = len(re.findall(r'(?<!\\)"', s))
    if quotes % 2 != 0:
        s += '"'

    # Remove dangling keys or trailing commas
    s = re.sub(r',\s*$', '', s)

    # Balance brackets
    stack = []
    in_str = False
    esc = False
    for ch in s:
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if not in_str:
            if ch in ('{', '['):
                stack.append(ch)
            elif ch == '}' and stack and stack[-1] == '{':
                stack.pop()
            elif ch == ']' and stack and stack[-1] == '[':
                stack.pop()

    for ch in reversed(stack):
        if ch == '{':
            s += '}'
        elif ch == '[':
            s += ']'

    return s


def parse_or_repair_document_structure(raw_text: str, fallback_title: str = "SOVA Technical Report") -> DocumentStructure:
    """
    Attempts to extract, repair, and parse structured JSON from LLM output.
    If JSON is missing, partially truncated, or malformed, gracefully repairs it.
    Falls back to Markdown parser if no JSON structure is detected.
    Guarantees a valid DocumentStructure is ALWAYS returned without crashing.
    """
    cleaned = raw_text.strip()

    # 1. Try exact code fence first
    fence_m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', cleaned)
    if fence_m:
        try:
            data = json.loads(fence_m.group(1))
            return DocumentStructure(**data)
        except Exception:
            pass

    # 2. Find starting brace
    idx = cleaned.find('{')
    if idx != -1:
        json_candidate = cleaned[idx:]
        json_candidate = re.sub(r'```\s*$', '', json_candidate).strip()

        # Direct parse attempt
        try:
            data = json.loads(json_candidate)
            return DocumentStructure(**data)
        except Exception:
            pass

        # Repaired parse attempt
        repaired = repair_truncated_json(json_candidate)
        try:
            data = json.loads(repaired)
            return DocumentStructure(**data)
        except Exception:
            pass

        # Progressive backward trim to find last valid closure
        pos = len(json_candidate)
        while pos > 0:
            last_brace = json_candidate.rfind('}', 0, pos)
            if last_brace == -1:
                break
            sub = json_candidate[:last_brace + 1]
            rep = repair_truncated_json(sub)
            try:
                data = json.loads(rep)
                return DocumentStructure(**data)
            except Exception:
                pos = last_brace

    # 3. Fallback to Markdown parser
    return parse_markdown_to_structure(raw_text, fallback_title)


class DocumentGenerationResult:
    def __init__(
        self,
        doc_id: str,
        title: str,
        subtitle: Optional[str],
        formats: List[str],
        page_count: int,
        files: Dict[str, Dict[str, Any]],
        created_at: str
    ):
        self.doc_id = doc_id
        self.title = title
        self.subtitle = subtitle
        self.formats = formats
        self.page_count = page_count
        self.files = files
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.doc_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "formats": self.formats,
            "page_count": self.page_count,
            "files": self.files,
            "created_at": self.created_at
        }


class DocumentService:
    """
    Central service for document generation, persistence, and downloads.
    """

    @staticmethod
    def generate_documents(
        structure: DocumentStructure,
        requested_formats: Optional[List[str]] = None
    ) -> DocumentGenerationResult:
        """
        Generates DOCX and/or PDF documents from a DocumentStructure model.
        Persists files locally and records metadata.
        """
        if not requested_formats:
            requested_formats = ["pdf", "docx"]

        requested_formats = [f.lower().strip() for f in requested_formats]
        # Normalize format names
        gen_pdf = "pdf" in requested_formats
        gen_docx = any(f in requested_formats for f in ["docx", "word", "doc"])

        if not gen_pdf and not gen_docx:
            gen_pdf = True
            gen_docx = True

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        doc_dir = GENERATED_DOCS_DIR / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        base_filename = sanitize_filename(structure.title)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        files_meta: Dict[str, Dict[str, Any]] = {}
        actual_page_count = 1
        active_formats: List[str] = []

        # 1. Generate DOCX if requested
        if gen_docx:
            docx_name = f"{base_filename}.docx"
            docx_path = doc_dir / docx_name
            try:
                generate_docx(structure, str(docx_path))
                size_b = docx_path.stat().st_size
                files_meta["docx"] = {
                    "format": "docx",
                    "filename": docx_name,
                    "download_url": f"/api/documents/generated/{doc_id}/download?format=docx",
                    "size_bytes": size_b,
                    "size_formatted": format_bytes(size_b),
                    "local_path": str(docx_path)
                }
                active_formats.append("docx")
                logger.info(f"Generated DOCX: {docx_path} ({size_b} bytes)")
            except Exception as e:
                logger.error(f"DOCX generation failed: {e}", exc_info=True)

        # 2. Generate PDF if requested
        if gen_pdf:
            pdf_name = f"{base_filename}.pdf"
            pdf_path = doc_dir / pdf_name
            try:
                generate_pdf(structure, str(pdf_path))
                size_b = pdf_path.stat().st_size

                # Count real PDF pages via PyMuPDF
                try:
                    pdf_doc = pymupdf.open(str(pdf_path))
                    actual_page_count = len(pdf_doc)
                    pdf_doc.close()
                except Exception:
                    actual_page_count = max(1, len(structure.sections))

                files_meta["pdf"] = {
                    "format": "pdf",
                    "filename": pdf_name,
                    "download_url": f"/api/documents/generated/{doc_id}/download?format=pdf",
                    "size_bytes": size_b,
                    "size_formatted": format_bytes(size_b),
                    "local_path": str(pdf_path)
                }
                active_formats.append("pdf")
                logger.info(f"Generated PDF: {pdf_path} ({size_b} bytes, {actual_page_count} pages)")
            except Exception as e:
                logger.error(f"PDF generation failed: {e}", exc_info=True)

        if not files_meta:
            raise RuntimeError("Failed to generate any requested document format.")

        # Estimate page count if PDF was not generated
        if not gen_pdf:
            # Estimate from sections and paragraphs (~3 paragraphs per page)
            total_elements = sum(len(s.paragraphs) + len(s.bullet_points) + len(s.tables) for s in structure.sections)
            actual_page_count = max(1, (total_elements // 4) + 1)

        result = DocumentGenerationResult(
            doc_id=doc_id,
            title=structure.title,
            subtitle=structure.subtitle,
            formats=active_formats,
            page_count=actual_page_count,
            files=files_meta,
            created_at=now_iso
        )

        # Save metadata to disk & cache in registry
        meta_file = doc_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

        _DOCUMENT_REGISTRY[doc_id] = result.to_dict()
        return result

    @staticmethod
    def get_generated_document(doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata of a previously generated document."""
        if doc_id in _DOCUMENT_REGISTRY:
            return _DOCUMENT_REGISTRY[doc_id]

        meta_file = GENERATED_DOCS_DIR / doc_id / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _DOCUMENT_REGISTRY[doc_id] = data
                    return data
            except Exception as e:
                logger.error(f"Error loading document metadata {meta_file}: {e}")

        return None

    @staticmethod
    def get_file_for_download(doc_id: str, fmt: str) -> Optional[Tuple[str, str, str]]:
        """
        Returns (local_file_path, download_filename, media_type) for downloading.
        """
        meta = DocumentService.get_generated_document(doc_id)
        if not meta:
            return None

        fmt_key = fmt.lower().strip()
        if fmt_key in ["doc", "word"]:
            fmt_key = "docx"

        file_info = meta.get("files", {}).get(fmt_key)
        if not file_info:
            return None

        local_path = file_info.get("local_path")
        if not local_path or not os.path.exists(local_path):
            # Check relative to doc_dir
            candidate = GENERATED_DOCS_DIR / doc_id / file_info["filename"]
            if candidate.exists():
                local_path = str(candidate)
            else:
                return None

        filename = file_info.get("filename", f"document.{fmt_key}")
        if fmt_key == "pdf":
            media_type = "application/pdf"
        elif fmt_key == "docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            media_type = "application/octet-stream"

        return local_path, filename, media_type
