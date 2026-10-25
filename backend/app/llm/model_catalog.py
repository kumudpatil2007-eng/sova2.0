from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from ..config import settings


class ModelPurpose(str, Enum):
    VISION = "vision"
    CODER = "coder"
    REASONING = "reasoning"
    DOCUMENT = "document"
    GENERAL = "general"


@dataclass
class ModelSpec:
    name: str
    purpose: ModelPurpose
    role_title: str
    description: str
    is_mandatory: bool = True
    vram_gb: float = 3.5
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose.value,
            "role_title": self.role_title,
            "description": self.description,
            "is_mandatory": self.is_mandatory,
            "vram_gb": self.vram_gb,
            "capabilities": self.capabilities,
        }


def get_default_model_catalog() -> Dict[ModelPurpose, ModelSpec]:
    """
    Returns the official catalog of supported local open-weight models for SOVA.
    Vision model explicitly set to qwen2.5vl:3b (NOT qwen2.5-vl:7b).
    """
    return {
        ModelPurpose.VISION: ModelSpec(
            name=settings.ollama_vision_model,  # qwen2.5vl:3b
            purpose=ModelPurpose.VISION,
            role_title="Multimodal P&ID & Visual Inspection",
            description="P&ID/image understanding, multimodal document analysis, visual inspection, extracting equipment tags, instruments, connections, labels.",
            is_mandatory=True,
            vram_gb=3.2,
            capabilities=["vision", "multimodal", "ocr_enhancement", "tag_extraction"]
        ),
        ModelPurpose.CODER: ModelSpec(
            name=settings.ollama_coder_model,  # qwen2.5-coder:7b
            purpose=ModelPurpose.CODER,
            role_title="Code Generation & Sandbox Computation",
            description="Code generation, code execution assistance, data-processing tasks, sandbox/code-related reasoning.",
            is_mandatory=True,
            vram_gb=4.7,
            capabilities=["code_generation", "python_sandbox", "tabular_transforms"]
        ),
        ModelPurpose.REASONING: ModelSpec(
            name=settings.ollama_reasoning_model,  # deepseek-r1:7b
            purpose=ModelPurpose.REASONING,
            role_title="Deep Engineering Reasoning & Synthesis",
            description="Deeper reasoning, multi-step engineering reasoning, evidence synthesis, cross-document reasoning.",
            is_mandatory=True,
            vram_gb=4.7,
            capabilities=["reasoning", "chain_of_thought", "cross_document_synthesis"]
        ),
        ModelPurpose.DOCUMENT: ModelSpec(
            name=settings.ollama_document_model,  # llama3.2:3b
            purpose=ModelPurpose.DOCUMENT,
            role_title="General Document & SOP Intelligence",
            description="General text/document Q&A, SOP/document retrieval responses, lightweight conversational tasks.",
            is_mandatory=True,
            vram_gb=2.0,
            capabilities=["document_qa", "sop_retrieval", "conversation", "summarization"]
        ),
        ModelPurpose.GENERAL: ModelSpec(
            name=settings.ollama_general_model,  # gemma2:9b
            purpose=ModelPurpose.GENERAL,
            role_title="General-Purpose Fallback",
            description="Optional general-purpose fallback model (non-mandatory).",
            is_mandatory=False,
            vram_gb=5.4,
            capabilities=["conversation", "general_reasoning"]
        ),
    }


def normalize_model_name(name: str) -> str:
    """Normalizes model names for robust comparison (e.g., 'qwen2.5vl:3b' vs 'qwen2.5vl:3b')."""
    return name.strip().lower()


def find_matching_installed_model(target: str, installed_models: List[str]) -> Optional[str]:
    """
    Finds the exact or best match in installed_models for target.
    Prevents confusing 'qwen2.5vl:3b' with 'qwen2.5-vl:7b' or 'qwen2.5vl:7b'.
    """
    target_clean = normalize_model_name(target)
    
    # 1. Exact match
    for m in installed_models:
        if normalize_model_name(m) == target_clean:
            return m

    # 2. Tag match where target might not have ':latest' but installed does or vice versa
    if ":" in target_clean:
        target_base, target_tag = target_clean.split(":", 1)
        for m in installed_models:
            m_clean = normalize_model_name(m)
            if ":" in m_clean:
                m_base, m_tag = m_clean.split(":", 1)
                # Ensure tag matches (crucial for 3b vs 7b distinction)
                if m_base == target_base and m_tag == target_tag:
                    return m
    else:
        # Target has no tag, look for match with ':latest'
        for m in installed_models:
            m_clean = normalize_model_name(m)
            if m_clean == f"{target_clean}:latest" or m_clean.split(":")[0] == target_clean:
                return m

    return None
