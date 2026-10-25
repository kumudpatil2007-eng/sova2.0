import asyncio
import os
import re
import sys
import json
import logging
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import pymupdf
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.llm.router import route_query, TaskCategory, detect_document_generation_intent
from app.services.document_generator import (
    DocumentService,
    DocumentStructure,
    DocumentSection,
    DocumentTable,
    DocumentCodeBlock,
    generate_docx,
    generate_pdf,
    parse_or_repair_document_structure
)
from app.services.document_processor import process_document, get_cached_document
from app.services.llm_service import generate_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_docgen")


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f" {title}")
    print("=" * 75)


async def main():
    print_banner("SOVA DOCUMENT GENERATION (DOCX & PDF) TEST SUITE")
    client = TestClient(app)

    # -------------------------------------------------------------------------
    # TEST 1: Normal Question: "What is 2 + 2?"
    # Expected: Normal answer, NO document generation triggered.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 1] Testing Normal Question: 'What is 2 + 2?'...")
    query_1 = "What is 2 + 2?"
    intent_1 = detect_document_generation_intent(query_1)
    decision_1 = route_query(query_1)

    assert intent_1 is None, f"Expected intent to be None for normal math question, got {intent_1}"
    assert decision_1.category != TaskCategory.DOCUMENT_GENERATION, f"Unexpected category: {decision_1.category}"
    assert not decision_1.is_document_generation, "is_document_generation must be False for normal chat"

    res_1 = await generate_response(query_1)
    assert res_1.get("generated_document") is None, "Normal chat must NOT generate a document"
    assert "4" in res_1["answer"], f"Expected '4' in answer, got: {res_1['answer']}"
    print(f"    Answer: {res_1['answer'].strip()}")
    print("    [PASSED] Test 1: Normal question returned direct answer with ZERO document generation.")

    # -------------------------------------------------------------------------
    # TEST 2: "Create a PDF explaining artificial intelligence."
    # Expected: Valid downloadable PDF, no DOCX.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 2] Testing PDF Request: 'Create a PDF explaining artificial intelligence.'...")
    query_2 = "Create a PDF explaining artificial intelligence."
    intent_2 = detect_document_generation_intent(query_2)
    assert intent_2 is not None, "Intent detection failed for PDF request"
    assert intent_2["formats"] == ["pdf"], f"Expected formats ['pdf'], got {intent_2['formats']}"

    decision_2 = route_query(query_2)
    assert decision_2.category == TaskCategory.DOCUMENT_GENERATION
    assert decision_2.is_document_generation is True
    assert decision_2.requested_formats == ["pdf"]

    res_2 = await generate_response(query_2)
    gen_doc_2 = res_2.get("generated_document")
    assert gen_doc_2 is not None, "Generated document metadata missing from response"
    assert "pdf" in gen_doc_2["files"], "PDF file metadata missing"
    assert "docx" not in gen_doc_2["files"], "DOCX should not be generated when only PDF requested"

    pdf_path_2 = gen_doc_2["files"]["pdf"]["local_path"]
    assert os.path.exists(pdf_path_2), f"PDF file not found at {pdf_path_2}"
    assert os.path.getsize(pdf_path_2) > 500, "PDF file is suspiciously small"

    # Verify PDF with PyMuPDF
    pdf_obj_2 = pymupdf.open(pdf_path_2)
    assert len(pdf_obj_2) >= 1, "PDF should have at least 1 page"
    pdf_text_2 = "".join(p.get_text() for p in pdf_obj_2)
    pdf_obj_2.close()
    assert "artificial intelligence" in pdf_text_2.lower() or "intelligence" in pdf_text_2.lower()

    # Test download endpoint
    dl_res_2 = client.get(f"/api/documents/generated/{gen_doc_2['id']}/download?format=pdf")
    assert dl_res_2.status_code == 200, f"Download failed with status {dl_res_2.status_code}"
    assert dl_res_2.headers["content-type"] == "application/pdf"
    assert len(dl_res_2.content) == os.path.getsize(pdf_path_2)

    print(f"    Document Title: {gen_doc_2['title']}")
    print(f"    PDF Path:       {pdf_path_2} ({gen_doc_2['files']['pdf']['size_formatted']})")
    print(f"    Download URL:   {gen_doc_2['files']['pdf']['download_url']}")
    print("    [PASSED] Test 2: Valid downloadable PDF generated and verified via PyMuPDF.")

    # -------------------------------------------------------------------------
    # TEST 3: "Create a Word document explaining artificial intelligence."
    # Expected: Valid downloadable DOCX, no PDF.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 3] Testing DOCX Request: 'Create a Word document explaining artificial intelligence.'...")
    query_3 = "Create a Word document explaining artificial intelligence."
    intent_3 = detect_document_generation_intent(query_3)
    assert intent_3 is not None, "Intent detection failed for DOCX request"
    assert intent_3["formats"] == ["docx"], f"Expected formats ['docx'], got {intent_3['formats']}"

    res_3 = await generate_response(query_3)
    gen_doc_3 = res_3.get("generated_document")
    assert gen_doc_3 is not None, "Generated document metadata missing"
    assert "docx" in gen_doc_3["files"], "DOCX file metadata missing"
    assert "pdf" not in gen_doc_3["files"], "PDF should not be generated when only DOCX requested"

    docx_path_3 = gen_doc_3["files"]["docx"]["local_path"]
    assert os.path.exists(docx_path_3), f"DOCX file not found at {docx_path_3}"

    # Verify DOCX with python-docx
    doc_obj_3 = docx.Document(docx_path_3)
    assert len(doc_obj_3.paragraphs) >= 3, "DOCX should have multiple paragraphs"
    docx_text_3 = " ".join(p.text for p in doc_obj_3.paragraphs)
    assert "intelligence" in docx_text_3.lower() or "ai" in docx_text_3.lower()

    # Test download endpoint
    dl_res_3 = client.get(f"/api/documents/generated/{gen_doc_3['id']}/download?format=docx")
    assert dl_res_3.status_code == 200, f"Download failed with status {dl_res_3.status_code}"
    assert "wordprocessingml" in dl_res_3.headers["content-type"]
    assert len(dl_res_3.content) == os.path.getsize(docx_path_3)

    print(f"    Document Title: {gen_doc_3['title']}")
    print(f"    DOCX Path:      {docx_path_3} ({gen_doc_3['files']['docx']['size_formatted']})")
    print(f"    Download URL:   {gen_doc_3['files']['docx']['download_url']}")
    print("    [PASSED] Test 3: Valid downloadable DOCX generated and verified via python-docx.")

    # -------------------------------------------------------------------------
    # TEST 4: "Create both a PDF and DOCX about machine learning."
    # Expected: Both files generated and downloadable.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 4] Testing Dual Generation: 'Create both a PDF and DOCX about machine learning.'...")
    query_4 = "Create both a PDF and DOCX about machine learning."
    intent_4 = detect_document_generation_intent(query_4)
    assert intent_4 is not None
    assert "pdf" in intent_4["formats"] and "docx" in intent_4["formats"]

    res_4 = await generate_response(query_4)
    gen_doc_4 = res_4.get("generated_document")
    assert gen_doc_4 is not None
    assert "pdf" in gen_doc_4["files"], "PDF missing in dual generation"
    assert "docx" in gen_doc_4["files"], "DOCX missing in dual generation"

    pdf_p4 = gen_doc_4["files"]["pdf"]["local_path"]
    docx_p4 = gen_doc_4["files"]["docx"]["local_path"]
    assert os.path.exists(pdf_p4) and os.path.exists(docx_p4)

    dl_pdf_4 = client.get(f"/api/documents/generated/{gen_doc_4['id']}/download?format=pdf")
    dl_docx_4 = client.get(f"/api/documents/generated/{gen_doc_4['id']}/download?format=docx")
    assert dl_pdf_4.status_code == 200 and dl_docx_4.status_code == 200

    print(f"    Document Title: {gen_doc_4['title']}")
    print(f"    PDF:            {gen_doc_4['files']['pdf']['filename']} ({gen_doc_4['files']['pdf']['size_formatted']})")
    print(f"    DOCX:           {gen_doc_4['files']['docx']['filename']} ({gen_doc_4['files']['docx']['size_formatted']})")
    print("    [PASSED] Test 4: Both PDF and DOCX generated successfully and both downloads verified.")

    # -------------------------------------------------------------------------
    # TEST 5: Upload Document + "Summarize this document and create a PDF."
    # Expected: The uploaded document is analyzed and summary PDF is generated.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 5] Testing Document-based PDF: 'Summarize this document and create a PDF.'...")
    # Load sample inspection document
    sample_path = BACKEND_DIR.parent / "sample_data" / "Heat_Exchanger_E204_Inspection_Report.pdf"
    if not sample_path.exists():
        sample_path = BACKEND_DIR / "sample_data" / "Heat_Exchanger_E204_Inspection_Report.pdf"

    assert sample_path.exists(), f"Sample report not found at {sample_path}"
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    doc_info = await process_document(str(sample_path), "Heat_Exchanger_E204_Inspection_Report.pdf", "sample_test_doc_001")
    file_id = doc_info["file_id"]
    cached_doc = get_cached_document(file_id)
    assert cached_doc is not None, "Failed to cache document"

    query_5 = "Summarize this document and create a PDF."
    res_5 = await generate_response(
        user_message=query_5,
        context=cached_doc.get("full_text", "")[:3500],
        doc_data=cached_doc
    )

    gen_doc_5 = res_5.get("generated_document")
    assert gen_doc_5 is not None, "Document generation failed for uploaded file summary"
    assert "pdf" in gen_doc_5["files"], "PDF not generated"

    pdf_p5 = gen_doc_5["files"]["pdf"]["local_path"]
    pdf_obj_5 = pymupdf.open(pdf_p5)
    text_p5 = "".join(p.get_text() for p in pdf_obj_5)
    pdf_obj_5.close()

    # Grounding check: should contain Heat Exchanger or E-204
    assert any(k in text_p5 for k in ["E-204", "Heat Exchanger", "thickness", "Inspection"]), "Summary PDF not grounded in document"
    print(f"    Generated PDF:  {gen_doc_5['files']['pdf']['filename']} ({gen_doc_5['files']['pdf']['size_formatted']})")
    print("    [PASSED] Test 5: Uploaded document analyzed and summary PDF generated with grounded facts.")

    # -------------------------------------------------------------------------
    # TEST 6: Upload Document + "Create a DOCX report from this document."
    # Expected: Valid DOCX based on the uploaded document.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 6] Testing Document-based DOCX: 'Create a DOCX report from this document.'...")
    query_6 = "Create a DOCX report from this document."
    res_6 = await generate_response(
        user_message=query_6,
        context=cached_doc.get("full_text", "")[:3500],
        doc_data=cached_doc
    )

    gen_doc_6 = res_6.get("generated_document")
    assert gen_doc_6 is not None, "Document generation failed"
    assert "docx" in gen_doc_6["files"], "DOCX not generated"

    docx_p6 = gen_doc_6["files"]["docx"]["local_path"]
    doc_obj_6 = docx.Document(docx_p6)
    text_p6 = " ".join(p.text for p in doc_obj_6.paragraphs)

    assert any(k in text_p6 for k in ["E-204", "Heat Exchanger", "Corrosion", "Inspection"]), "DOCX not grounded in document"
    print(f"    Generated DOCX: {gen_doc_6['files']['docx']['filename']} ({gen_doc_6['files']['docx']['size_formatted']})")
    print("    [PASSED] Test 6: Valid DOCX report created from uploaded document.")

    # -------------------------------------------------------------------------
    # TEST 7: Generate Long Multi-Page Document
    # Expected: Multiple pages with proper formatting, headers, footers, tables.
    # -------------------------------------------------------------------------
    print("\n>>> [TEST 7] Testing Long Multi-Page Document Generation...")
    long_sections = [
        DocumentSection(
            heading="1. Executive Summary & Facility Context",
            level=1,
            paragraphs=[
                "This comprehensive technical assessment report establishes the mechanical integrity and remaining safe operating lifespan for Heat Exchanger E-204 located within Crude Distillation Unit CDU-1.",
                "All calculations adhere strictly to API 579-1 / ASME FFS-1 Fitness-For-Service standards, ASME Section VIII Division 1 Boiler and Pressure Vessel Code, and plant reliability mandates."
            ],
            bullet_points=[
                "Assessment Standard: API 579-1 Part 4 (General Metal Loss) Level 1 Assessment",
                "Operating Pressure: 18.2 bar design / 14.5 bar normal operating threshold",
                "Operating Temperature: 185 deg C inlet / 130 deg C outlet"
            ],
            page_break_after=True
        ),
        DocumentSection(
            heading="2. Ultrasonic Thickness Measurement (UTM) Empirical Data",
            level=1,
            paragraphs=[
                "Ultrasonic thickness inspection was completed on 18 September 2026 across 24 critical Thickness Measurement Locations (TMLs). The nominal specification is SA-516 Gr. 70 carbon steel with nominal wall thickness of 10.0 mm."
            ],
            tables=[
                DocumentTable(
                    caption="Summary of Critical TML Inspection Points",
                    headers=["TML Tag", "Location / Component", "Nominal (mm)", "Measured (mm)", "Loss (mm)", "Corrosion Rate (mm/yr)"],
                    rows=[
                        ["TML-01", "Shell Course 1 Top", "10.0", "9.6", "0.4", "0.08"],
                        ["TML-07", "Shell Course 2 Bottom", "10.0", "9.1", "0.9", "0.12"],
                        ["TML-14", "Channel Side Inlet", "10.0", "8.2", "1.8", "0.15"],
                        ["TML-19", "Channel Side Return Nozzle", "10.0", "8.4", "1.6", "0.14"],
                        ["TML-24", "Floating Head Cover", "12.0", "11.2", "0.8", "0.09"],
                    ]
                )
            ],
            page_break_after=True
        ),
        DocumentSection(
            heading="3. Mathematical Modeling & Code Computations",
            level=1,
            paragraphs=[
                "The minimum required retirement wall thickness (t_min) is determined per ASME Section VIII Division 1 UG-27 equation for cylindrical shells under internal design pressure:"
            ],
            code_blocks=[
                DocumentCodeBlock(
                    language="python",
                    code="""# API 579-1 Level 1 Calculation for Cylindrical Shell
P = 18.2          # Design Pressure (bar)
R = 600.0         # Inside Radius (mm)
S = 138.0         # Allowable Stress for SA-516 Gr.70 (MPa)
E = 1.0           # Joint Efficiency (Full Radiography)

# t_min = (P * R) / (S * E - 0.6 * P)
t_min = (1.82 * 600.0) / (138.0 * 1.0 - 0.6 * 1.82)
# Result: t_min = 7.02 mm (Design Retirement Limit: 7.0 mm)
remaining_ca = 8.2 - 7.0  # Remaining Corrosion Allowance = 1.2 mm
remaining_life = remaining_ca / 0.15  # Remaining Life = 8.0 Years"""
                )
            ],
            numbered_list=[
                "1. Step 1: Compute circumferential hoop stress and minimum thickness requirement (7.0 mm).",
                "2. Step 2: Establish remaining corrosion allowance across governing location TML-14 (1.2 mm).",
                "3. Step 3: Compute remaining operating lifespan based on maximum observed corrosion rate (8.0 years)."
            ],
            page_break_after=True
        ),
        DocumentSection(
            heading="4. Engineering Recommendations & Action Plan",
            level=1,
            paragraphs=[
                "Heat Exchanger E-204 is approved for continued safe operation under current design conditions. However, the localized thinning at TML-14 requires increased inspection frequency.",
                "An ultrasonic reinspection is scheduled for Q3 2027 to verify that corrosion rates do not accelerate."
            ],
            bullet_points=[
                "Next Inspection Date: September 2027 (12-month interval)",
                "Action Item: Install online ultrasonic corrosion monitoring sensors at TML-14 and TML-19",
                "Corrosion Inhibitor: Maintain neutralizer dosing at CDU overhead accumulator to minimize acid condensation"
            ]
        )
    ]

    long_doc = DocumentStructure(
        title="Comprehensive Mechanical Integrity & Fitness-For-Service Assessment Report",
        subtitle="Crude Distillation Unit (CDU-1) — Heat Exchanger E-204",
        author="SOVA Industrial Reliability & Mechanical Integrity Division",
        organization="Refinery Engineering Operations",
        confidentiality="Confidential • Strictly Air-Gapped",
        summary="A formal 4-part fitness-for-service evaluation of Heat Exchanger E-204 per API 579-1. Evaluates ultrasonic thickness readings, corrosion rates, remaining safe operating life, and scheduled maintenance requirements.",
        sections=long_sections
    )

    long_result = DocumentService.generate_documents(long_doc, ["pdf", "docx"])
    assert long_result.page_count >= 3, f"Expected long document to have >= 3 pages, got {long_result.page_count}"

    # Verify PDF page flow and header/footer
    long_pdf_path = long_result.files["pdf"]["local_path"]
    long_pdf_obj = pymupdf.open(long_pdf_path)
    assert len(long_pdf_obj) >= 3, f"PDF page count should be >= 3, got {len(long_pdf_obj)}"

    # Check footer page strings
    last_page_text = long_pdf_obj[-1].get_text()
    assert f"of {len(long_pdf_obj)}" in last_page_text, "Dynamic page counter 'Page X of Y' failed in PDF"
    long_pdf_obj.close()

    print(f"    Long Document Page Count: {long_result.page_count} pages")
    print(f"    PDF Size:                 {long_result.files['pdf']['size_formatted']}")
    print(f"    DOCX Size:                {long_result.files['docx']['size_formatted']}")
    print("    [PASSED] Test 7: Multi-page document flows across pages with professional typography and page numbers.")

    print_banner("ALL 7 TESTS SUCCESSFULLY PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
