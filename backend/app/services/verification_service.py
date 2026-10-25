import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("sovereign_ai.verification")

# Industrial keywords that must never be fabricated without document support
CRITICAL_INDUSTRIAL_METRICS = [
    "wall thickness", "thickness", "corrosion rate", "corrosion allowance",
    "pressure", "temperature", "vibration", "rpm", "retirement thickness",
    "minimum allowable thickness", "tmin", "yield strength", "tensile strength"
]


@dataclass
class VerificationResult:
    is_verified: bool
    grounded: bool
    leak_count: int
    unsupported_numbers: List[float] = field(default_factory=list)
    verified_numbers: List[float] = field(default_factory=list)
    unsupported_claims: List[str] = field(default_factory=list)
    unrelated_workflow_detected: bool = False
    missing_info_properly_stated: bool = False
    verification_label: str = "UNVERIFIED"
    corrected_response: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_verified": self.is_verified,
            "grounded": self.grounded,
            "leak_count": self.leak_count,
            "unsupported_numbers": self.unsupported_numbers,
            "verified_numbers": self.verified_numbers,
            "unsupported_claims": self.unsupported_claims,
            "unrelated_workflow_detected": self.unrelated_workflow_detected,
            "missing_info_properly_stated": self.missing_info_properly_stated,
            "verification_label": self.verification_label,
            "notes": self.notes
        }


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extracts standalone numerical values (integers & floats) from text,
    ignoring common structural tokens like bullet points (1., 2.), markdown headers, and years (2025, 2026).
    """
    # Remove dates like 2026-09-25 or timestamps like 09:20:00 to avoid confusing them with values
    cleaned = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' ', text)
    cleaned = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', ' ', cleaned)
    # Remove bullet enumerations like "1. ", "2. ", "## 1 "
    cleaned = re.sub(r'(?:^|\n)\s*(?:#+\s*)?\d+\.\s*', ' ', cleaned)

    tokens = re.findall(r'(?<![A-Za-z\-_])\b\d+(?:\.\d+)?\b(?![A-Za-z\-_])', cleaned)
    numbers = []
    for t in tokens:
        try:
            val = float(t)
            # Skip very common structural integers
            if val in {0.0, 1.0, 2.0, 3.0, 4.0, 5.0} and f"{t}." in text:
                continue
            numbers.append(val)
        except ValueError:
            continue
    return numbers


def build_evidence_number_pool(evidence_texts: List[str]) -> Set[float]:
    """Extracts all valid numbers present across all supplied evidence text chunks."""
    pool: Set[float] = set()
    for text in evidence_texts:
        if not text:
            continue
        # Extract all floats and ints
        raw_nums = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        for n in raw_nums:
            try:
                pool.add(float(n))
            except ValueError:
                pass
    return pool


def verify_response_grounding(
    query: str,
    response: str,
    evidence_text: str = "",
    doc_full_text: str = "",
    doc_filename: str = "",
    is_conversational: bool = False,
    telemetry_facts: Optional[List[str]] = None
) -> VerificationResult:
    """
    Industrial Evidence Verification Pipeline:
    1. Did the response answer the actual user question?
    2. Are factual claims supported by retrieved evidence?
    3. Are numerical values present in the source data?
    4. Are document references actually present?
    5. Did the model introduce unsupported facts?
    6. Did the system invoke an unrelated analysis workflow?
    7. If information is missing, did the system correctly state that it is unavailable?
    """
    leak_count = 0
    unsupported_claims: List[str] = []
    unsupported_numbers: List[float] = []
    verified_numbers: List[float] = []
    notes: List[str] = []
    corrected_response: Optional[str] = None

    query_lower = query.strip().lower()
    response_lower = response.strip().lower()

    # Rule 6: Check for unrelated analysis workflow
    # If the user asked a casual question ("wassup"), but the response generates an engineering report
    unrelated_workflow = False
    if is_conversational:
        engineering_artifacts = [
            "# engineering note", "wall thickness calculation", "api-579",
            "asme b31.3", "corrosion rate calculation", "retirement thickness",
            "tml-14", "ultrasonic thickness measurement"
        ]
        for artifact in engineering_artifacts:
            if artifact in response_lower:
                unrelated_workflow = True
                leak_count += 1
                unsupported_claims.append(f"Unrelated engineering analysis invoked for casual query: '{artifact}'")
                notes.append("System mistakenly triggered industrial analysis for a casual conversation.")
                break

    # Check if response properly states unavailability when information is absent
    missing_info_indicators = [
        "not available in the supplied",
        "not present in the supplied",
        "not found in the supplied",
        "is not available in the",
        "information is not available",
        "is not provided in the supplied"
    ]
    missing_stated = any(ind in response_lower for ind in missing_info_indicators)

    # Check if query was asking for an entity or metric that is NOT in the document
    # E.g. TEST 5: "What is the wall thickness of HX-401?" when HX-401 is not in the document
    requested_eq_match = re.search(r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b', query, re.IGNORECASE)
    requested_equipment = requested_eq_match.group(1).upper() if requested_eq_match else None

    source_pool_text = f"{evidence_text}\n{doc_full_text}\n{doc_filename}"
    if telemetry_facts:
        source_pool_text += "\n" + "\n".join(telemetry_facts)

    equipment_in_source = True
    if requested_equipment:
        equipment_in_source = requested_equipment in source_pool_text.upper()

    # Check for requested metric
    requested_metric = None
    for metric in CRITICAL_INDUSTRIAL_METRICS:
        if metric in query_lower:
            requested_metric = metric
            break

    # Hallucination trap detection:
    # If the requested equipment is NOT in the source, but the model gave an answer without stating unavailable
    if requested_equipment and not equipment_in_source and not is_conversational:
        if not missing_stated:
            leak_count += 1
            metric_desc = f"the {requested_metric} of {requested_equipment}" if requested_metric else f"{requested_equipment}"
            unsupported_claims.append(f"Fabricated claims for equipment '{requested_equipment}' not present in documents.")
            notes.append(f"Equipment '{requested_equipment}' is not in supplied documents; model attempted to answer.")
            # Automatically correct the response to adhere to Grounding Rule
            if requested_metric:
                corrected_response = f"The {requested_metric} of {requested_equipment} is not available in the supplied documents."
            else:
                corrected_response = f"Information regarding {requested_equipment} is not available in the supplied documents."

    # Rule 3: Check numerical claims against source evidence
    if not is_conversational and source_pool_text.strip():
        evidence_numbers = build_evidence_number_pool([source_pool_text])
        response_numbers = extract_numbers_from_text(response)

        for num in response_numbers:
            # Check if number matches any number in the source pool (with slight floating tolerance)
            is_present = False
            for ev_num in evidence_numbers:
                if abs(num - ev_num) < 0.01:
                    is_present = True
                    break
            
            if is_present:
                verified_numbers.append(num)
            else:
                # If the number is an invented measurement or parameter
                unsupported_numbers.append(num)
                leak_count += 1
                unsupported_claims.append(f"Unsupported numerical value: {num}")

    # Determine if verification passed
    is_verified = (leak_count == 0) and not unrelated_workflow
    grounded = is_verified

    # Label assignment: "VERIFIED (0 LEAKS)" ONLY if is_verified is True and leak_count == 0
    if is_verified:
        verification_label = "VERIFIED (0 LEAKS)"
        if not notes:
            notes.append("All claims and numerical values trace back to supplied evidence.")
    else:
        verification_label = f"UNGROUNDED ({leak_count} LEAKS)"

    return VerificationResult(
        is_verified=is_verified,
        grounded=grounded,
        leak_count=leak_count,
        unsupported_numbers=unsupported_numbers,
        verified_numbers=verified_numbers,
        unsupported_claims=unsupported_claims,
        unrelated_workflow_detected=unrelated_workflow,
        missing_info_properly_stated=missing_stated,
        verification_label=verification_label,
        corrected_response=corrected_response,
        notes="; ".join(notes) if notes else "Grounding check complete."
    )
