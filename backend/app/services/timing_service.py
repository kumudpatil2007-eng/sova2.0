import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("sovereign_ai.timing")


class PipelineTimer:
    """
    Instruments the end-to-end local inference pipeline to measure bottlenecks:
    1. File upload time
    2. PDF extraction time
    3. OCR time
    4. Image rendering time
    5. Prompt/context construction time
    6. Ollama request start
    7. Time to first token
    8. Total model generation time
    9. Total response time
    """
    def __init__(self, operation_name: str = "Inference"):
        self.operation_name = operation_name
        self.t_start = time.perf_counter()
        
        self.file_upload_time: float = 0.0
        self.extraction_time: float = 0.0
        self.ocr_time: float = 0.0
        self.image_render_time: float = 0.0
        self.context_time: float = 0.0
        
        self.ollama_start_time: Optional[float] = None
        self.time_to_first_token: Optional[float] = None
        self.llm_generation_time: float = 0.0
        self.total_response_time: float = 0.0
        
        self.is_cached: bool = False
        self.routing_decision: str = "text"
        self.model_used: str = "qwen2.5vl:3b"

    def mark_ollama_start(self):
        self.ollama_start_time = time.perf_counter()

    def mark_first_token(self):
        if self.ollama_start_time and self.time_to_first_token is None:
            self.time_to_first_token = time.perf_counter() - self.ollama_start_time

    def finish_generation(self):
        if self.ollama_start_time:
            self.llm_generation_time = time.perf_counter() - self.ollama_start_time
        self.total_response_time = time.perf_counter() - self.t_start
        self.log_measurements()

    def log_measurements(self):
        first_token_str = f"{self.time_to_first_token:.2f}s" if self.time_to_first_token is not None else "N/A"
        cached_str = " (cached)" if self.is_cached else ""
        
        log_lines = [
            f"--- [Pipeline Bottleneck Instrumentation: {self.operation_name}] ---",
            f"[Route] pipeline: {self.routing_decision.upper()} -> Model: {self.model_used}{cached_str}",
            f"[Document] extraction: {self.extraction_time:.2f}s",
            f"[OCR] processing: {self.ocr_time:.2f}s",
            f"[Image] rendering: {self.image_render_time:.2f}s",
            f"[Context] construction: {self.context_time:.2f}s",
            f"[LLM] time to first token: {first_token_str}",
            f"[LLM] generation: {self.llm_generation_time:.2f}s",
            f"[Total] {self.total_response_time:.2f}s",
            "------------------------------------------------------------------"
        ]
        
        for line in log_lines:
            logger.info(line)
            # Also print directly to ensure developer terminal displays it prominently
            print(line)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_cached": self.is_cached,
            "routing": self.routing_decision,
            "model": self.model_used,
            "extraction_s": round(self.extraction_time, 2),
            "ocr_s": round(self.ocr_time, 2),
            "image_render_s": round(self.image_render_time, 2),
            "context_s": round(self.context_time, 2),
            "time_to_first_token_s": round(self.time_to_first_token, 2) if self.time_to_first_token is not None else None,
            "llm_generation_s": round(self.llm_generation_time, 2),
            "total_s": round(self.total_response_time, 2),
        }
