import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from ..config import settings
from .model_catalog import ModelPurpose, get_default_model_catalog

logger = logging.getLogger("sovereign_ai.router")


class TaskCategory(str, Enum):
    CASUAL = "casual"
    VISION_PID = "vision_pid"
    TELEMETRY = "telemetry"
    REASONING = "reasoning"
    CODING = "coding"
    DOCUMENT_QA = "document_qa"
    DOCUMENT_GENERATION = "document_generation"


@dataclass
class RoutingDecision:
    category: TaskCategory
    model_purpose: ModelPurpose
    model_name: str
    requires_vision: bool
    requires_telemetry_engine: bool
    system_prompt: str
    reason: str
    deterministic_answer: Optional[str] = None
    telemetry_facts: List[str] = field(default_factory=list)
    is_document_generation: bool = False
    requested_formats: List[str] = field(default_factory=list)


# Task-specific system prompts
PROMPT_CASUAL = """You are SOVA, an on-premise sovereign industrial AI assistant.
Respond politely, concisely, and conversationally.
Do NOT generate engineering reports, inspection notes, or fabricate equipment calculations unless explicitly requested.
If a document is attached, simply acknowledge it and ask what specific analysis or question the user has."""

PROMPT_VISION_PID = """You are SOVA Vision, specialized in technical drawings, P&IDs, and visual inspection.
Strict Grounding Rules:
1. Identify ONLY equipment, tags (e.g. P-101, V-201, HX-301), instruments (PT, TT, FT, LT), valves, and flow lines that are VISIBLE in the diagram.
2. If an equipment tag or instrument is NOT visible, explicitly state that it is not visible.
3. NEVER invent equipment numbers, design pressures, or pipe sizes.
4. Clearly distinguish equipment, instruments, and lines."""

PROMPT_TELEMETRY = """You are SOVA Telemetry Analyst.
Strict Grounding Rules:
1. Base all conclusions strictly on the exact numerical values provided in the telemetry evidence.
2. If a specific timestamp, equipment parameter, or reading was not recorded or is missing, explicitly state: "This information is not available in the supplied documents/data."
3. NEVER invent or extrapolate missing measurements, sensor readings, or timestamps."""

PROMPT_REASONING = """You are SOVA Deep Reasoning Engine (powered by DeepSeek-R1).
Your task is rigorous multi-step engineering analysis and cross-document evidence synthesis.
Strict Grounding Rules:
1. Synthesize evidence from both technical diagrams (P&ID) and empirical data (telemetry).
2. Every factual and numerical claim MUST trace back to the supplied evidence. Cite the exact readings, timestamps, and equipment tags.
3. If an explanation requires missing measurements or unrecorded parameters, explicitly state that the data is not available rather than assuming values.
4. Show your step-by-step engineering reasoning clearly."""

PROMPT_CODER = """You are SOVA Code & Sandbox Specialist.
Write clean, robust, and self-contained Python code to process engineering datasets, parse telemetry, or calculate equations.
Do not assume external internet access or cloud libraries."""

PROMPT_DOCUMENT = """You are SOVA Document Assistant.
Strict Grounding Rules:
1. Answer strictly using the excerpts provided from the uploaded document/SOP.
2. If the requested information is not contained in the excerpts, respond: "This information is not available in the supplied documents/data."
3. Never invent measurements, wall thicknesses, corrosion rates, or standards."""

PROMPT_GENERAL = """You are SOVA, an on-premise sovereign industrial and technical AI assistant.
Answer the user's question directly, accurately, and concisely.
If asked general mathematical questions (e.g. "What is 2 + 2?"), scientific principles, or definitions (e.g. "What is machine learning?"), provide the exact, direct answer without fabricating unrelated engineering reports."""

PROMPT_DOCUMENT_GENERATION = """You are SOVA Document Generation Intelligence.
Your task is to author professional, publication-grade technical and engineering reports.
You MUST format your document content strictly as JSON wrapped inside ```json ... ``` code fences.

JSON Structure:
{
  "title": "Comprehensive Document Title",
  "subtitle": "Clear Subtitle or Topic Focus",
  "author": "SOVA Sovereign Intelligence",
  "date": "2026-09-26",
  "organization": "SOVA Industrial Systems",
  "confidentiality": "Confidential - Air-Gapped Internal",
  "summary": "Executive summary summarizing the document's objectives, findings, and key takeaways.",
  "sections": [
    {
      "heading": "1. Section Heading",
      "level": 1,
      "paragraphs": [
        "In-depth technical paragraph explaining the topic thoroughly with clear explanations.",
        "Second detailed paragraph expanding on the architecture, methodology, or principles."
      ],
      "bullet_points": [
        "Key operational parameter or requirement",
        "Critical finding or technical specification"
      ],
      "numbered_list": [
        "1. Step or procedural phase 1",
        "2. Step or procedural phase 2"
      ],
      "tables": [
        {
          "caption": "Technical Overview / Comparison",
          "headers": ["Item / Parameter", "Specification / Value", "Status / Notes"],
          "rows": [
            ["Component A", "Value / Spec 1", "Operational"],
            ["Component B", "Value / Spec 2", "Verified"]
          ]
        }
      ],
      "code_blocks": [
        {
          "language": "python",
          "code": "# Relevant sample code or calculation"
        }
      ],
      "page_break_after": false
    }
  ]
}

Strict Report Authoring Rules:
1. Provide rich, extensive multi-paragraph content across multiple logical sections (e.g., Introduction, Technical Architecture, Core Capabilities, Engineering Analysis, Best Practices & Summary).
2. If an uploaded document is provided, ground all facts, equipment tags, readings, and conclusions strictly in that context.
3. If no document is uploaded, generate an authoritative, structured, and comprehensive report on the requested subject.
4. Always include at least 1 formatted table and structured bullet points to ensure a professional publication layout.
5. Strictly output ONLY the JSON structure within ```json ... ``` fences."""


def is_casual_query(query: str) -> bool:
    """Detects casual greetings and conversational banter."""
    q = query.strip().lower()
    # Remove punctuation
    q_clean = re.sub(r'[^a-z0-9\s]', '', q)
    casual_words = {
        "wassup", "whatsup", "whats up", "sup", "hello", "hi", "hey",
        "hey there", "good morning", "good afternoon", "good evening",
        "who are you", "what are you", "how are you", "test", "testing",
        "thanks", "thank you", "bye", "goodbye"
    }
    if q_clean in casual_words:
        return True

    # Check for short greetings
    tokens = q_clean.split()
    if len(tokens) <= 3 and any(t in {"hi", "hello", "hey", "wassup", "yo"} for t in tokens):
        return True

    return False


def is_general_query(query: str) -> bool:
    """
    Detects normal text-only questions, general knowledge, math calculations,
    and standard programming theory queries that do NOT target the uploaded document.
    e.g. '2 + 2', 'What is 2 + 2?', 'Explain recursion.', 'Explain binary search',
         'What is machine learning?', 'Summarize this text.'
    """
    q = query.strip().lower()

    # Simple arithmetic: "2 + 2", "what is 2 + 2", "5 * 10", etc.
    if re.search(r'^\s*(what\s+is\s+)?\d+\s*[\+\-\*\/\^]\s*\d+', q):
        return True

    # General conceptual explanations & programming theory
    general_patterns = [
        r'\b(explain|what is|how does)\s+(recursion|binary search|quicksort|sorting|machine learning|deep learning|bubble sort|polymorphism|inheritance|oop|rest api|hash table|linked list)\b',
        r'^(what is\s+)?2\s*\+\s*2\??$',
        r'^explain\s+(binary search|recursion|merge sort)\.?$',
        r'^summarize\s+this\s+text\.?$'
    ]
    if any(re.search(pat, q) for pat in general_patterns):
        return True

    return False


def detect_document_generation_intent(query: str) -> Optional[Dict[str, Any]]:
    """
    Detects if user is requesting document / report / PDF / DOCX generation.
    Returns dict with target formats and flags, or None if normal chat.
    """
    q = query.strip().lower()

    # Exclude casual greetings
    if is_casual_query(q):
        return None

    # Check for negative patterns (asking questions about a document without requesting creation)
    if re.search(r'^(what\s+is\s+in|what\s+does|can\s+you\s+read|tell\s+me\s+about\s+this|show\s+me)\b', q) and not re.search(r'\b(create|generate|make|export|convert|produce|draft|write|download)\b', q):
        return None

    # Explicit format mentions
    has_pdf = bool(re.search(r'\b(pdf|adobe)\b', q))
    has_docx = bool(re.search(r'\b(docx?|word(\s+doc(ument)?)?)\b', q))
    has_both = bool(re.search(r'\bboth\b', q)) or (has_pdf and has_docx)

    # Document generation action triggers
    action_patterns = [
        r'\b(create|generate|make|produce|draft|build|write|export|convert|output)\b.*?\b(pdf|docx?|word|report|summary\s+document|project\s+report|document|file)\b',
        r'\b(as|in|into|to)\s+(a\s+)?(pdf|docx?|word(\s+doc(ument)?)?|report|document)\b',
        r'\bdownloadable\s+(pdf|docx?|word|report|document|file)\b',
        r'\b\d+[- ]page\s+(report|summary|document)\b',
        r'\bsummary\b.*?\b(as|in|into)\b.*?\b(pdf|docx?|word)\b',
        r'\bconvert\b.*?\b(into|to|as)\b.*?\b(pdf|docx?|word|report)\b'
    ]

    is_doc_gen = any(re.search(pat, q) for pat in action_patterns)
    if not is_doc_gen:
        return None

    formats = []
    if has_both:
        formats = ["pdf", "docx"]
    elif has_pdf and not has_docx:
        formats = ["pdf"]
    elif has_docx and not has_pdf:
        formats = ["docx"]
    else:
        formats = ["pdf", "docx"]

    return {
        "is_document_generation": True,
        "formats": formats,
        "has_pdf": "pdf" in formats,
        "has_docx": "docx" in formats
    }


def route_query(
    query: str,
    doc_data: Optional[Dict[str, Any]] = None,
    doc_extension: str = "",
    doc_has_images: bool = False,
    telemetry_result: Optional[Dict[str, Any]] = None
) -> RoutingDecision:
    """
    Intelligent Model Router for SOVA:
    Determines task category, optimal model, and system prompt.
    Adheres strictly to the model routing rule:
    - Normal text-only questions -> llama3.2:3b
    - Multimodal / visual document requests -> qwen2.5vl:3b
    - Never send image/multimodal content to llama3.2:3b
    """
    catalog = get_default_model_catalog()
    q = query.strip()
    q_lower = q.lower()

    # Category A1: Casual Conversation
    if is_casual_query(q):
        model_name = catalog[ModelPurpose.DOCUMENT].name  # llama3.2:3b for lightweight conversation
        return RoutingDecision(
            category=TaskCategory.CASUAL,
            model_purpose=ModelPurpose.DOCUMENT,
            model_name=model_name,
            requires_vision=False,
            requires_telemetry_engine=False,
            system_prompt=PROMPT_CASUAL,
            reason="Casual greeting/conversation: routed to llama3.2:3b."
        )

    # Category A2: Normal text-only questions (Math, General Theory, Recursion, etc.)
    # (Works even when a document is attached in workspace)
    if is_general_query(q):
        model_name = catalog[ModelPurpose.DOCUMENT].name  # llama3.2:3b
        return RoutingDecision(
            category=TaskCategory.CASUAL,
            model_purpose=ModelPurpose.DOCUMENT,
            model_name=model_name,
            requires_vision=False,
            requires_telemetry_engine=False,
            system_prompt=PROMPT_GENERAL,
            reason="Normal text-only query: routed to llama3.2:3b without document constraints."
        )

    # Category 0: Document Generation (PDF/DOCX) Request
    doc_intent = detect_document_generation_intent(q)
    if doc_intent:
        formats = doc_intent["formats"]
        format_desc = " and ".join(f.upper() for f in formats)

        # Check if the document requires visual understanding (scanned PDF, image file, technical drawing)
        doc_needs_vision = bool(
            (doc_data and (doc_data.get("requires_vision") or doc_data.get("is_scanned"))) or
            (doc_extension in {".png", ".jpg", ".jpeg", ".webp"})
        )

        if doc_needs_vision:
            # Multimodal document: routed to qwen2.5vl:3b with vision tensors
            model_name = catalog[ModelPurpose.VISION].name  # qwen2.5vl:3b
            m_purpose = ModelPurpose.VISION
            req_vision = True
            reason_str = f"Document generation request for {format_desc} from multimodal/scanned document: routed to {model_name}."
        else:
            # Text-based document: routed to llama3.2:3b with pure text context. NEVER send vision tensors to llama3.2:3b!
            model_name = catalog[ModelPurpose.DOCUMENT].name  # llama3.2:3b
            m_purpose = ModelPurpose.DOCUMENT
            req_vision = False
            reason_str = f"Document generation request for {format_desc} from text document: routed to {model_name}."

        return RoutingDecision(
            category=TaskCategory.DOCUMENT_GENERATION,
            model_purpose=m_purpose,
            model_name=model_name,
            requires_vision=req_vision,
            requires_telemetry_engine=telemetry_result is not None,
            system_prompt=PROMPT_DOCUMENT_GENERATION,
            reason=reason_str,
            is_document_generation=True,
            requested_formats=formats
        )

    # Category E: Coding & Sandbox Tasks
    coding_triggers = [
        "write a python", "write python", "python script", "generate code",
        "write a function", "write script", "code to calculate", "program to"
    ]
    if any(t in q_lower for t in coding_triggers):
        model_name = catalog[ModelPurpose.CODER].name  # qwen2.5-coder:7b
        return RoutingDecision(
            category=TaskCategory.CODING,
            model_purpose=ModelPurpose.CODER,
            model_name=model_name,
            requires_vision=False,
            requires_telemetry_engine=False,
            system_prompt=PROMPT_CODER,
            reason="Coding/sandbox query: routed to qwen2.5-coder:7b."
        )

    # Category D: Deep Reasoning & Cross-Document Synthesis
    reasoning_triggers = [
        "using the p&id and telemetry", "using pid and telemetry",
        "using both", "cross-document", "why may have approached",
        "explain why", "root cause", "identify abnormal equipment and explain the evidence",
        "relationship between vibration", "degradation before the trip",
        "synthesize", "failure analysis"
    ]
    if any(t in q_lower for t in reasoning_triggers):
        model_name = catalog[ModelPurpose.REASONING].name  # deepseek-r1:7b
        doc_has_visual = bool(doc_has_images or (doc_data and doc_data.get("requires_vision")))
        return RoutingDecision(
            category=TaskCategory.REASONING,
            model_purpose=ModelPurpose.REASONING,
            model_name=model_name,
            requires_vision=doc_has_visual,
            requires_telemetry_engine=True,
            system_prompt=PROMPT_REASONING,
            reason="Multi-step engineering reasoning / cross-document synthesis: routed to deepseek-r1:7b."
        )

    # Category C: CSV/XLSX Telemetry Questions
    is_telemetry_doc = doc_extension in {".csv", ".xlsx", ".xls"}
    telemetry_query_triggers = [
        "pressure of", "temperature of", "vibration of", "highest vibration",
        "maximum temperature", "maximum recorded temperature", "trip condition",
        "time did", "at 09:", "at 9:", "alarm state", "abnormal equipment"
    ]
    if is_telemetry_doc or (telemetry_result and telemetry_result.get("status") in {"EXACT_MATCH", "AGGREGATE_MATCH"}):
        model_name = catalog[ModelPurpose.DOCUMENT].name  # llama3.2:3b for summarizing verified facts
        return RoutingDecision(
            category=TaskCategory.TELEMETRY,
            model_purpose=ModelPurpose.DOCUMENT,
            model_name=model_name,
            requires_vision=False,
            requires_telemetry_engine=True,
            system_prompt=PROMPT_TELEMETRY,
            reason="Telemetry data query: routed to deterministic engine + llama3.2:3b for factual response."
        )

    # Category B: Multimodal / Image / Scanned Document / P&ID Understanding
    pid_triggers = [
        "p&id", "pid", "drawing", "diagram", "equipment is shown", "equipment present in this p&id",
        "identify all pumps", "pumps and vessels", "flow path", "instruments associated with",
        "what equipment is present", "where is pt-", "where is tt-", "flow line", "piping",
        "analyze this scanned", "scanned pdf", "scanned document", "visual inspection",
        "look at the image", "in the diagram", "in the drawing", "schematic", "chart"
    ]
    has_visual_doc = bool(
        doc_has_images or
        (doc_data and (doc_data.get("requires_vision") or doc_data.get("is_scanned"))) or
        (doc_extension in {".png", ".jpg", ".jpeg", ".webp"}) or
        (doc_extension == ".pdf" and any(k in (doc_data.get("filename", "") + q_lower) for k in ["pid", "p_and_id", "p&id", "drawing", "diagram"]))
    )

    query_needs_vision = any(t in q_lower for t in pid_triggers)
    doc_primarily_visual = bool(
        doc_data and (
            doc_data.get("is_scanned") or
            doc_data.get("requires_vision") or
            (doc_extension in {".png", ".jpg", ".jpeg", ".webp"})
        )
    )

    if query_needs_vision or doc_primarily_visual:
        model_name = catalog[ModelPurpose.VISION].name  # qwen2.5vl:3b
        return RoutingDecision(
            category=TaskCategory.VISION_PID,
            model_purpose=ModelPurpose.VISION,
            model_name=model_name,
            requires_vision=True,
            requires_telemetry_engine=False,
            system_prompt=PROMPT_VISION_PID,
            reason="Multimodal/visual document query: routed to qwen2.5vl:3b with image input."
        )

    # Category F: General Text Document / SOP Questions vs Normal Chat
    has_any_doc = bool(doc_data and (doc_data.get("full_text") or doc_data.get("filename") or doc_data.get("df") is not None))
    model_name = catalog[ModelPurpose.DOCUMENT].name  # llama3.2:3b

    if has_any_doc:
        return RoutingDecision(
            category=TaskCategory.DOCUMENT_QA,
            model_purpose=ModelPurpose.DOCUMENT,
            model_name=model_name,
            requires_vision=False,
            requires_telemetry_engine=False,
            system_prompt=PROMPT_DOCUMENT,
            reason="General document/SOP query: routed to RAG + llama3.2:3b (text only)."
        )
    else:
        # No document attached: normal conversational and general technical Q&A
        return RoutingDecision(
            category=TaskCategory.CASUAL,
            model_purpose=ModelPurpose.DOCUMENT,
            model_name=model_name,
            requires_vision=False,
            requires_telemetry_engine=False,
            system_prompt=PROMPT_GENERAL,
            reason="Normal chat/general technical query without attached document: routed to llama3.2:3b."
        )
