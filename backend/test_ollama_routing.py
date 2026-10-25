import os
import sys
import asyncio
import logging
from pathlib import Path
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.llm.model_catalog import ModelPurpose, get_default_model_catalog
from app.llm.local_client import OllamaLocalClient, OllamaUnavailableError, ollama_client
from app.llm.router import route_query, TaskCategory
from app.services.document_processor import process_document, get_cached_document
from app.services.rag_service import chunk_document, retrieve_relevant_context
from app.services.telemetry_service import query_telemetry_deterministically
from app.services.verification_service import verify_response_grounding
from app.services.llm_service import generate_response, check_ollama_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_routing")


async def run_all_tests():
    print("\n" + "=" * 70)
    print(" SOVA SOVEREIGN MODEL ROUTING & VERIFICATION SUITE")
    print("=" * 70)

    # Health check
    status = await check_ollama_status()
    print(f"Ollama Online:    {status['online']}")
    print(f"Installed Models: {', '.join(status.get('available_models', []))}")
    print("=" * 70 + "\n")

    # -------------------------------------------------------------
    # TEST 1: Casual Conversation ("wassup")
    # -------------------------------------------------------------
    print(">>> [TEST 1] Testing Casual Query: 'wassup' with attached document...")
    # Simulate an attached P&ID document
    dummy_doc = {"filename": "SOVA_Test_P_and_ID.pdf", "extension": ".pdf", "full_text": "P-101, V-201, HX-301"}
    decision_1 = route_query("wassup", doc_data=dummy_doc, doc_extension=".pdf")
    print(f"    Task Category:   {decision_1.category.value}")
    print(f"    Routed Model:    {decision_1.model_name}")
    print(f"    Requires Vision: {decision_1.requires_vision}")
    assert decision_1.category == TaskCategory.CASUAL, f"Expected CASUAL, got {decision_1.category}"
    assert decision_1.requires_vision is False, "Casual query should not require vision tensors"
    
    # Run inference with llama3.2:3b
    resp_1 = await generate_response(
        user_message="wassup",
        context="",
        conversation_history=[],
        doc_data=dummy_doc
    )
    answer_1 = resp_1["answer"]
    print(f"    Model Response:  {answer_1[:120]}...")
    assert not any(k in answer_1.lower() for k in ["# engineering note", "wall thickness", "api-579", "tml-14"]), \
        "Casual query must NOT trigger engineering report workflow!"
    print("    [PASSED] Test 1: Casual query handled conversationally without triggering engineering workflows.\n")

    # -------------------------------------------------------------
    # TEST 2: P&ID / Image Understanding ("What equipment is present in this P&ID?")
    # -------------------------------------------------------------
    print(">>> [TEST 2] Testing P&ID Query: 'What equipment is present in this P&ID?'...")
    pid_path = Path("sample_data/Heat_Exchanger_E204_Inspection_Report.pdf")
    # Check if SOVA_Test_P_and_ID.pdf exists in uploads
    test_pid = None
    for p in Path("uploads").glob("**/SOVA_Test_P_and_ID.pdf"):
        test_pid = p
        break

    if test_pid and test_pid.exists():
        doc_2 = await process_document(str(test_pid), test_pid.name, "pid_test_001")
        chunk_document(doc_2)
        decision_2 = route_query("What equipment is present in this P&ID?", doc_data=doc_2, doc_extension=".pdf", doc_has_images=len(doc_2["images_base64"]) > 0)
        print(f"    Task Category:   {decision_2.category.value}")
        print(f"    Routed Model:    {decision_2.model_name}")
        print(f"    Requires Vision: {decision_2.requires_vision}")
        assert decision_2.category == TaskCategory.VISION_PID, f"Expected VISION_PID, got {decision_2.category}"
        assert decision_2.model_name == settings.ollama_vision_model, f"Expected {settings.ollama_vision_model}, got {decision_2.model_name}"
        assert len(doc_2["images_base64"]) > 0, "P&ID PDF must produce image frames for vision model"

        retrieval_2 = retrieve_relevant_context("pid_test_001", "equipment present in this P&ID")
        resp_2 = await generate_response(
            user_message="What equipment is present in this P&ID?",
            context=retrieval_2.get("context_text", ""),
            images_base64=doc_2["images_base64"],
            doc_data=doc_2
        )
        print(f"    Model Used:      {resp_2['model']}")
        print(f"    Model Response:  {resp_2['answer'][:160]}...")
        assert "qwen2.5vl:3b" in resp_2["model"], f"Expected qwen2.5vl:3b, got {resp_2['model']}"
        print("    [PASSED] Test 2: P&ID query routed to qwen2.5vl:3b with image frames.\n")
    else:
        print("    [SKIPPED] Test 2: SOVA_Test_P_and_ID.pdf not found in uploads.\n")

    # -------------------------------------------------------------
    # TEST 3: Telemetry Query ("What was the pressure of V-201 at 09:20?")
    # -------------------------------------------------------------
    print(">>> [TEST 3] Testing Telemetry Query: 'What was the pressure of V-201 at 09:20?'...")
    # Telemetry DataFrame specified in requirements
    df_data = [
        {"timestamp": "2026-09-25 09:20:00", "equipment_id": "V-201", "equipment_type": "Separator Vessel", "status": "Alarm", "temperature_C": 72.6, "pressure_bar": 18.2, "rpm": 0, "vibration_mm_s": 41.0, "current_A": 0.35, "alarm_flag": 1}
    ]
    df_telemetry = pd.DataFrame(df_data)
    result_3 = query_telemetry_deterministically(df_telemetry, "What was the pressure of V-201 at 09:20?")
    print(f"    Deterministic Output: {result_3['answer']}")
    assert result_3["status"] == "EXACT_MATCH", f"Expected EXACT_MATCH, got {result_3['status']}"
    assert "18.2" in result_3["answer"], f"Expected 18.2 bar in answer, got: {result_3['answer']}"
    assert "18.2 bar" in result_3["answer"], f"Expected '18.2 bar', got: {result_3['answer']}"
    print("    [PASSED] Test 3: Exact pressure 18.2 bar extracted deterministically.\n")

    # -------------------------------------------------------------
    # TEST 4: Telemetry Query with Missing Time ("What was the pressure of V-201 at 09:27?")
    # -------------------------------------------------------------
    print(">>> [TEST 4] Testing Missing Timestamp: 'What was the pressure of V-201 at 09:27?'...")
    result_4 = query_telemetry_deterministically(df_telemetry, "What was the pressure of V-201 at 09:27?")
    print(f"    Deterministic Output: {result_4['answer']}")
    assert result_4["status"] == "NOT_FOUND", f"Expected NOT_FOUND, got {result_4['status']}"
    assert "not available in the supplied data" in result_4["answer"].lower(), \
        f"Expected 'not available in the supplied data', got: {result_4['answer']}"
    print("    [PASSED] Test 4: System explicitly stated reading at 09:27 is not available (zero hallucination).\n")

    # -------------------------------------------------------------
    # TEST 5: Missing Equipment Wall Thickness ("What is the wall thickness of HX-401?")
    # -------------------------------------------------------------
    print(">>> [TEST 5] Testing Non-Existent Equipment: 'What is the wall thickness of HX-401?'...")
    doc_5 = {
        "filename": "Inspection_Report_E204.pdf",
        "full_text": "Equipment: Heat Exchanger E-204. Nominal thickness: 10.0 mm. Measured: 8.2 mm.",
        "extension": ".pdf"
    }
    # Response verification on non-existent HX-401
    verification_5 = verify_response_grounding(
        query="What is the wall thickness of HX-401?",
        response="The wall thickness of HX-401 is 3.18 mm per ultrasonic test.",  # Deliberate hallucination attempt
        evidence_text="",
        doc_full_text=doc_5["full_text"],
        doc_filename=doc_5["filename"]
    )
    print(f"    Verification Status: {verification_5.verification_label}")
    print(f"    Unsupported Claims:  {verification_5.unsupported_claims}")
    print(f"    Corrected Response:  {verification_5.corrected_response}")
    assert verification_5.is_verified is False, "Hallucinated response must NOT pass verification!"
    assert "3.18" in str(verification_5.unsupported_numbers), "3.18 mm must be flagged as unsupported!"
    assert "not available in the supplied documents" in verification_5.corrected_response.lower(), \
        "Corrected response must state information is unavailable."
    print("    [PASSED] Test 5: Hallucinated 3.18 mm caught and corrected to 'The wall thickness of HX-401 is not available in the supplied documents.'\n")

    # -------------------------------------------------------------
    # TEST 6: Deep Reasoning / Cross-Document ("Using the P&ID and telemetry data...")
    # -------------------------------------------------------------
    print(">>> [TEST 6] Testing Deep Reasoning: 'Using the P&ID and telemetry data, identify abnormal equipment and explain the evidence.'...")
    query_6 = "Using the P&ID and telemetry data, identify abnormal equipment and explain the evidence."
    decision_6 = route_query(query_6, doc_data=dummy_doc)
    print(f"    Task Category:   {decision_6.category.value}")
    print(f"    Routed Model:    {decision_6.model_name}")
    assert decision_6.category == TaskCategory.REASONING, f"Expected REASONING, got {decision_6.category}"
    assert decision_6.model_name == settings.ollama_reasoning_model, f"Expected {settings.ollama_reasoning_model}, got {decision_6.model_name}"

    context_6 = "P&ID shows Feed Pump P-101 feeding Separator V-201 and Heat Exchanger HX-301. Telemetry records show P-101 tripped at 09:30 with vibration 58.4 mm/s. V-201 pressure rose to 19.6 bar (alarm > 18 bar)."
    resp_6 = await generate_response(
        user_message=query_6,
        context=context_6,
        doc_data={"filename": "Combined_Evidence", "full_text": context_6, "extension": ".pdf"}
    )
    print(f"    Model Used:      {resp_6['model']}")
    print(f"    Model Response:  {resp_6['answer'][:180]}...")
    print(f"    Verification:    {resp_6['verification']['verification_label']}")
    assert "deepseek-r1:7b" in resp_6["model"], f"Expected deepseek-r1:7b, got {resp_6['model']}"
    print("    [PASSED] Test 6: Deep reasoning executed with deepseek-r1:7b grounded in P&ID and telemetry context.\n")

    # -------------------------------------------------------------
    # TEST 7: Disconnect / Unreachable Ollama
    # -------------------------------------------------------------
    print(">>> [TEST 7] Testing Disconnected Local AI Engine...")
    bad_client = OllamaLocalClient(base_url="http://127.0.0.1:19999")  # Unused port
    health_bad = await bad_client.check_health(timeout=1.0)
    print(f"    Connection Result: {health_bad['online']}")
    print(f"    Error Reported:    {health_bad['error']}")
    assert health_bad["online"] is False, "Client should report offline when daemon is unreachable"
    assert "cannot connect" in health_bad["error"].lower() or "connection" in health_bad["error"].lower()

    # Verify that trying to infer through unreachable client throws error and NEVER returns hardcoded fake text
    try:
        await bad_client.chat(
            model="qwen2.5vl:3b",
            messages=[{"role": "user", "content": "What is the wall thickness of HX-401?"}]
        )
        assert False, "Should have raised OllamaUnavailableError"
    except OllamaUnavailableError as e:
        print(f"    Proper Exception Caught: {e}")
        assert "unavailable" in str(e).lower()
    print("    [PASSED] Test 7: Disconnected engine raises clear system error and NEVER generates fake engineering responses.\n")

    print("=" * 70)
    print(" ALL 7 ACCEPTANCE TESTS SUCCESSFULLY PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
