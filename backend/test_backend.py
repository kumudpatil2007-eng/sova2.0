import asyncio
from pathlib import Path
from app.services.file_service import save_uploaded_file, UPLOAD_ROOT
from app.services.document_processor import process_document
from app.services.rag_service import chunk_document, retrieve_relevant_context
from app.services.llm_service import check_ollama_status
from app.routes.system import system_status

async def test_pipeline():
    print("Testing System Status Endpoint...")
    status = await system_status()
    print("System Status:", status)

    sample_pdf = Path("sample_data/Heat_Exchanger_E204_Inspection_Report.pdf")
    if sample_pdf.exists():
        print("\nTesting PDF extraction on sample PDF...")
        doc = await process_document(str(sample_pdf), sample_pdf.name, "test_file_001")
        print(f"Extracted {doc['total_pages']} pages, {len(doc['full_text'])} characters.")
        
        chunks = chunk_document(doc)
        print(f"Generated {len(chunks)} chunks.")

        retrieval = retrieve_relevant_context("test_file_001", "What is the minimum measured thickness and corrosion rate?")
        print(f"Retrieved {len(retrieval['sources'])} sources.")
        for s in retrieval['sources']:
            print(f"  Source Page {s['page']}: {s['excerpt'][:80]}...")
    else:
        print("Sample PDF not found.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
