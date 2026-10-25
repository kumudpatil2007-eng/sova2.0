import re
import math
from typing import List, Dict, Any, Optional

class DocumentChunk:
    def __init__(self, chunk_id: str, page_number: int, text: str, file_id: str):
        self.chunk_id = chunk_id
        self.page_number = page_number
        self.text = text.strip()
        self.file_id = file_id

# In-memory index of chunks per file_id
_chunk_index: Dict[str, List[DocumentChunk]] = {}


def chunk_document(doc_data: Dict[str, Any], max_chunk_chars: int = 1000, overlap: int = 150) -> List[DocumentChunk]:
    file_id = doc_data["file_id"]
    chunks: List[DocumentChunk] = []
    chunk_counter = 0

    pages = doc_data.get("pages", [])
    if not pages and doc_data.get("full_text"):
        pages = [{"page_number": 1, "text": doc_data["full_text"]}]

    for page in pages:
        page_num = page.get("page_number", 1)
        page_text = page.get("text", "").strip()
        if not page_text:
            continue

        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', page_text)
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= max_chunk_chars:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(DocumentChunk(
                        chunk_id=f"{file_id}_{chunk_counter}",
                        page_number=page_num,
                        text=current_chunk,
                        file_id=file_id
                    ))
                    chunk_counter += 1

                # If single paragraph is larger than max_chunk_chars, split by sentences
                if len(para) > max_chunk_chars:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    sub_chunk = ""
                    for s in sentences:
                        if len(sub_chunk) + len(s) <= max_chunk_chars:
                            sub_chunk += (" " if sub_chunk else "") + s
                        else:
                            if sub_chunk:
                                chunks.append(DocumentChunk(
                                    chunk_id=f"{file_id}_{chunk_counter}",
                                    page_number=page_num,
                                    text=sub_chunk,
                                    file_id=file_id
                                ))
                                chunk_counter += 1
                            sub_chunk = s
                    current_chunk = sub_chunk
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(DocumentChunk(
                chunk_id=f"{file_id}_{chunk_counter}",
                page_number=page_num,
                text=current_chunk,
                file_id=file_id
            ))
            chunk_counter += 1

    _chunk_index[file_id] = chunks
    return chunks


def score_chunk(query_tokens: List[str], chunk_text: str) -> float:
    text_lower = chunk_text.lower()
    score = 0.0
    for token in query_tokens:
        if not token:
            continue
        # Exact word match
        matches = len(re.findall(r'\b' + re.escape(token) + r'\b', text_lower))
        if matches > 0:
            score += matches * 2.0
        elif token in text_lower:
            score += 0.5
    return score


def retrieve_relevant_context(
    file_id: str,
    query: str,
    top_k: int = 4
) -> Dict[str, Any]:
    chunks = _chunk_index.get(file_id, [])
    if not chunks:
        return {
            "context_text": "",
            "sources": []
        }

    # Tokenize query (alphanumeric words >= 3 chars, lowercased)
    stopwords = {"what", "which", "where", "when", "how", "this", "that", "the", "and", "for", "with", "from", "show", "tell", "about", "give", "report", "identify", "find"}
    raw_tokens = re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', query.lower())
    query_tokens = [t for t in raw_tokens if t not in stopwords]

    scored = []
    for chunk in chunks:
        score = score_chunk(query_tokens, chunk.text)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Pick top_k chunks with positive match score
    selected_chunks = [chunk for score, chunk in scored[:top_k] if score > 0]
    
    # If no keyword matches found, only fallback to overview chunks if no specific equipment tag was queried
    equipment_in_query = re.search(r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b', query, re.IGNORECASE)
    if not selected_chunks and chunks and not equipment_in_query:
        selected_chunks = chunks[:min(2, len(chunks))]

    context_parts = []
    sources = []
    seen_pages = set()

    for chunk in selected_chunks:
        context_parts.append(f"[Document Page {chunk.page_number} Excerpt]:\n{chunk.text}")
        if chunk.page_number not in seen_pages:
            seen_pages.add(chunk.page_number)
            sources.append({
                "page": chunk.page_number,
                "name": f"Page {chunk.page_number}",
                "type": "Inspection Document",
                "excerpt": (chunk.text[:180] + "...") if len(chunk.text) > 180 else chunk.text,
                "relevance": "High"
            })

    sources.sort(key=lambda s: s["page"])

    return {
        "context_text": "\n\n".join(context_parts),
        "sources": sources
    }
