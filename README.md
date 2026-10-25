# SOVA (Sovereign AI Workbench)

**A Sovereign, Air-Gapped AI Workbench for Confidential Industrial Engineering Documents**

SOVA is built for on-premise industrial plant environments (refineries, petrochemical complexes, offshore platforms) where technical drawings, ultrasonic thickness inspection reports, P&IDs, and equipment datasheets cannot leave company premises.

---

## 🔒 Sovereignty & Hardware Constraints

- **Hardware Target**: Development & Edge workstation with **NVIDIA GeForce RTX 4050 / 3050 (4–6 GB VRAM)**.
- **Local Ollama Daemon**: `http://127.0.0.1:11434`
- **External Calls**: **Strictly 0**. Zero cloud APIs (no OpenAI, Gemini, Anthropic, or external OCR services).
- **Document Processing**: 100% on-premise execution using **PyMuPDF**, local **Tesseract OCR**, **Pandas**, and local vector chunk retrieval.

---

## 🤖 Supported Local Open-Weight Models & Routing Architecture

SOVA incorporates a dynamic, intent-based local model router:

```
                         USER QUERY
                             │
                             ▼
                 INTENT / TASK CLASSIFICATION
                             │
                             ▼
                        MODEL ROUTER
                             │
       ┌──────────────┬──────┴───────┬──────────────┐
       ▼              ▼              ▼              ▼
  Casual Chat     P&ID / Vision   Telemetry     Deep Reasoning
  (llama3.2:3b)   (qwen2.5vl:3b)  (Pandas first) (deepseek-r1:7b)
       │              │              │              │
       └──────────────┴──────┬───────┴──────────────┘
                             ▼
                 Evidence-Grounded Response
                             │
                             ▼
                 7-Point Verification Check
                             │
                             ▼
                        Final Answer
```

### Model Roster:

1. **`qwen2.5vl:3b`** (Multimodal Vision):
   - **Purpose**: P&ID understanding, multimodal document analysis, visual inspection, extracting equipment tags (e.g. `P-101`, `V-201`), instruments (`PT-201`, `TT-201`), connections, and labels.
   - **Note**: Configured explicitly as `qwen2.5vl:3b` (NOT `qwen2.5-vl:7b`).

2. **`qwen2.5-coder:7b`** (Code & Computation):
   - **Purpose**: Code generation, execution assistance, data processing tasks, and sandbox computation.

3. **`deepseek-r1:7b`** (Deep Engineering Reasoning):
   - **Purpose**: Multi-step engineering reasoning, cross-document evidence synthesis, root cause failure analysis.

4. **`llama3.2:3b`** (General Document & SOP Intelligence):
   - **Purpose**: General text/document Q&A, SOP retrieval, and lightweight conversational greetings.

5. **`gemma2:9b`** (Optional General Fallback):
   - **Purpose**: Optional general-purpose fallback model (non-mandatory).

---


---

## 📄 Automated Document Generation (DOCX & PDF)

SOVA features an on-premise, publication-grade document generation engine supporting both Microsoft Word (`.docx`) and Adobe PDF (`.pdf`) without any external dependencies:

- **Strict Intent Discrimination**: Automatically differentiates casual queries (e.g. *"What is 2 + 2?"* -> answers `4`, zero files created) from document synthesis requests (e.g. *"Create a PDF report on heat exchangers"*, *"Summarize this into a DOCX"*).
- **Format Flexibility**: Generates standalone **PDF**, standalone **DOCX**, or **both formats concurrently** upon request.
- **Enterprise Typography**:
  - **DOCX**: Custom corporate palette (Deep Navy `#1A365D`, Slate `#2B6CB0`), styled title blocks, zebra-striped tables with repeated header rows, and formatted code blocks with light gray shading.
  - **PDF**: Two-pass dynamic `NumberedCanvas` (*"Page X of Y"*), automatic table wrapping across page splits, chunked multi-page code blocks, running headers and footers.
- **Interactive UI Download Cards**: Chat messages seamlessly render a dedicated download card displaying document metadata (title, summary, estimated page count, file size, air-gapped security badge) and direct download buttons.
- **Secure Endpoints**:
  - `POST /api/documents/generate`: Direct structured or freeform document generation.
  - `GET /api/documents/generated/{doc_id}`: Metadata retrieval.
  - `GET /api/documents/generated/{doc_id}/download?format=pdf|docx`: Streaming download with content-disposition attachment.

## 🛡️ Grounding & 7-Point Verification Pipeline

SOVA enforces strict hallucination prevention:

- **Grounding Rule**: 
  - IF requested information exists in supplied documents/data: answer using the evidence.
  - IF requested information does NOT exist: respond clearly:
    `"This information is not available in the supplied documents/data."`
- **Zero Fabrication**: Pressure, temperature, wall thickness, corrosion rate, equipment tags, manufacturer, SOP references, engineering limits, and timestamps are never invented.
- **7 Automated Checks**:
  1. Did the response answer the actual user question?
  2. Are factual claims supported by retrieved evidence?
  3. Are numerical values present in the source data?
  4. Are document references actually present?
  5. Did the model introduce unsupported facts?
  6. Did the system invoke an unrelated analysis workflow?
  7. If information is missing, did the system correctly state that it is unavailable?
- Responses receive a **`VERIFIED (0 LEAKS)`** certification only when fully grounded in source evidence.

---

## 🚀 Quickstart & Setup Guide

### Step 1: Install & Pull Ollama Models
Ensure Ollama is installed from [ollama.com](https://ollama.com):
```bash
ollama serve
ollama pull qwen2.5vl:3b
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
ollama pull llama3.2:3b
```

Verify installed models:
```bash
ollama list
```

### Step 2: Install Backend Dependencies
```powershell
cd backend
py -m pip install -r requirements.txt
```

### Step 3: Run Acceptance Test Suite
```powershell
cd backend
python test_ollama_routing.py
```
This tests all 7 operational scenarios end-to-end against real local models.

### Step 4: Launch SOVA
You can run `start.bat` at the repository root, or start components individually:

**Backend:**
```powershell
cd backend
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Frontend:**
```powershell
cd sovereign-ai
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🧪 Acceptance Test Suite (All 7 Cases)

| Test | Query / Scenario | Routed Model | Expected Result | Status |
|------|-------------------|--------------|-----------------|--------|
| **TEST 1** | `"wassup"` (with document) | `llama3.2:3b` | Conversational response, zero engineering reports | **PASSED** |
| **TEST 2** | `"What equipment is present in this P&ID?"` | `qwen2.5vl:3b` (Image frame) | Identifies visible equipment (`P-101`, `V-201`, `HX-301`) | **PASSED** |
| **TEST 3** | `"What was the pressure of V-201 at 09:20?"` | Deterministic Telemetry | Returns `18.2 bar` from telemetry row | **PASSED** |
| **TEST 4** | `"What was the pressure of V-201 at 09:27?"` | Deterministic Telemetry | Explicitly states reading at 09:27 is not available | **PASSED** |
| **TEST 5** | `"What is the wall thickness of HX-401?"` | Verification Grounding | Catch hallucination $\rightarrow$ states unavailable in docs | **PASSED** |
| **TEST 6** | Cross-document reasoning | `deepseek-r1:7b` | Synthesizes P&ID + telemetry; all claims trace to data | **PASSED** |
| **TEST 7** | Disconnected Ollama daemon | Error Isolation | Reports local engine offline, zero fake fallback data | **PASSED** |

---


### Document Generation Test Suite (`test_document_generation.py`)

| Test | Query / Scenario | Expected Result | Status |
|------|-------------------|-----------------|--------|
| **TEST 1** | Casual Chat (*"What is 2 + 2?"*) | Returns `4`, **0** files generated | **PASSED** |
| **TEST 2** | Standalone PDF Generation (*"Create a PDF explaining AI"*) | Generates valid, non-empty `.pdf` with title and page count | **PASSED** |
| **TEST 3** | Standalone DOCX Generation (*"Create a DOCX about Solar"*) | Generates valid `.docx` with headings, paragraphs, and tables | **PASSED** |
| **TEST 4** | Dual Generation (*"Create both a PDF and DOCX report on Robotics"*) | Generates both `.pdf` and `.docx` concurrently | **PASSED** |
| **TEST 5** | Document-Grounded PDF Summary | Synthesizes uploaded context into grounded summary PDF | **PASSED** |
| **TEST 6** | Document-Grounded DOCX Report | Synthesizes technical data into structured corporate DOCX | **PASSED** |
| **TEST 7** | Long Multi-Page Document (>2 Pages) | Clean pagination, no overflow, dynamic page numbers | **PASSED** |

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── config.py                # Centralized Pydantic configuration & .env loader
│   │   ├── main.py                  # FastAPI entrypoint, CORS & model registry sync
│   │   ├── llm/
│   │   │   ├── __init__.py          # Exported LLM components
│   │   │   ├── local_client.py      # Air-gapped Ollama client (streaming, lazy loading)
│   │   │   ├── model_catalog.py     # 5 open-weight model catalog & specifications
│   │   │   └── router.py            # Intent & task classification model router
│   │   ├── routes/
│   │   │   ├── upload.py            # POST /api/upload (multipart/form-data)
│   │   │   ├── chat.py              # POST /api/chat & /api/chat/stream
│   │   │   ├── system.py            # GET /api/system/status & /api/system/models
│   │   │   ├── documents.py         # Sample document retrieval
│   │   │   └── auth.py              # Local Argon2id authentication
│   │   └── services/
│   │       ├── document_processor.py# PyMuPDF, OCR, P&ID visual frames & Pandas
│   │       ├── telemetry_service.py # Deterministic CSV/XLSX telemetry query engine
│   │       ├── verification_service.py # 7-point evidence grounding verifier
│   │       ├── model_registry.py    # SQLite database model registry synchronizer
│   │       ├── llm_service.py       # Unified LLM orchestration service
│   │       ├── file_service.py      # Local file validation and storage
│   │       └── rag_service.py       # Chunking & page-level citation retriever
│   ├── test_ollama_routing.py       # Comprehensive 7-test acceptance test suite
│   ├── test_document_generation.py  # 7-test PDF & DOCX generation verification suite
│   ├── test_backend.py              # System status & extraction test
│   └── requirements.txt             # Python dependencies
├── sovereign-ai/                    # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/ChatMessage.tsx # Markdown renderer, model badge, verification badge
│   │   │   ├── status/SystemPanel.tsx # Live model routing & GPU status overlay
│   │   │   └── layout/TopBar.tsx    # Live Ollama connection status
│   │   ├── pages/
│   │   │   ├── Workspace.tsx        # Main AI workbench with streaming tokens
│   │   │   └── SystemPage.tsx       # System architecture & task routing display
│   │   └── services/api.ts          # Unified REST & SSE client
├── .env                             # Environment & model configuration
├── start.bat                        # One-click Windows startup script
└── README.md                        # Documentation & setup guide
```
