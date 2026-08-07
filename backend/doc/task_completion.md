**Yes, absolutely.** Keeping `tech_stack.md` synchronized with `backend_plan.md` ensures that your system architecture, data models, and component pipeline descriptions remain 100% consistent across all documentation files.

---

### 📝 What was added to `tech_stack.md`:

1. **Section 1 (Data Persistence & Smart Caching)**: Explicitly listed `jd_detail` (deep web market research) and `interview_behavior` (Eva's dynamic persona configuration) alongside `parsed_resume` and `parsed_jd` in the database schema specification.
2. **Section 2 (Artificial Intelligence & LLM Stack)**: Specified how Stage 1 generates `jd_detail`, how Stage 2 constructs `interview_behavior`, and how Stage 3 ingests both JSON objects to contextually steer the live Qwen 2.5 LLM during voice interviews.

---

Here is the complete, updated **`tech_stack.md`** file ready to copy and paste into your project:

```markdown
# Netran AI — Technical Stack Architecture

This document defines the complete technology stack powering **Netran AI**, an autonomous, real-time AI-powered technical interviewer platform.

---

## 🏗️ Core Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Next.js Web Frontend Client                           │
│             (React 18/19, Tailwind CSS, Web Audio Worklet API)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP REST (JSON) / WebSockets (Binary PCM)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Web API Gateway                              │
│         (Python 3.12 + Uvicorn + OAuth2 JWT + Smart SQLite Caching)         │
└──────┬───────────────┬───────────────┬───────────────┬───────────────┬──────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│ Auth & User  ││  Ingestion   ││ Stage 1 & 2  ││   Stage 3:   ││   Stage 4:   │
│ Management   ││ Engine (Resume││ Research &   ││ Live Voice   ││ Evaluation   │
│ (Bcrypt/JWT) ││ & JD Parsing)││ Question Tree││  (Local GPU) ││  (Multimodal)│
└──────────────┘└──────────────┘└──────────────┘└──────────────┘└──────────────┘

```

---

## ⚡ 1. Backend Service & API Layer

* **API Web Framework**: **FastAPI**
* Asynchronous Python web framework built on **Starlette** and **ASGI** (`uvicorn`).
* Interactive, auto-generated OpenAPI (Swagger UI) documentation served at `/docs`.
* Asynchronous background execution (`fastapi.BackgroundTasks` / `asyncio.to_thread`) for long-running AI pipeline tasks.
* Real-time, full-duplex streaming communication over **WebSockets** (`/api/v1/voice/stream/{session_id}`).
* Middleware suite incorporating `CORSMiddleware` (configuring Next.js cross-origin access) and request timing telemetry.


* **Ingestion & Data Normalization Endpoints**:
* **Resume Upload (`POST /api/v1/ingest/resume`)**: Accepts `multipart/form-data` uploads (`.pdf`, `.docx`, `.txt`, `.tex`), extracts raw text, processes it through Gemini JSON extraction, and outputs a structured `CandidateProfile` schema.
* **JD Text Ingestion (`POST /api/v1/ingest/jd`)**: Accepts pasted raw JD text, extracts core requirements, seniority, and tech stack, outputting a standardized `ParsedJD` schema.


* **Authentication & Authorization**: **OAuth2 + JWT (Production Standard)**
* Password hashing and verification using `passlib[bcrypt]` / `argon2`.
* Stateful session management and token handling with `python-jose` / `PyJWT`.
* Role-Based Access Control (RBAC) separating `candidate` endpoints from `admin` evaluation views.
* Query-parameter authentication support (`?token=...`) for native browser WebSocket handshakes.


* **Data Persistence & Smart Caching Engine**: **SQLAlchemy / SQLModel + SQLite 3**
* Persistent storage for user credentials, interview sessions, parsed JSON schemas, and stage output artifacts.
* **Session Artifacts Storage (`session_artifacts` table):** Native `JSON` columns storing `parsed_resume`, `parsed_jd`, `jd_detail` (deep web intelligence), `interview_behavior` (Eva persona rules), `question_tree`, `transcript`, and `evaluation_report` (`sessions/<session_id>/recording.wav` is the only binary file saved on disk).
* **Input-Hash Deduplication (Smart SQLite Caching):** Uses SHA-256 fingerprinting (`Resume + JD`) to prevent redundant Gemini/LLM calls if a candidate re-submits or re-opens a session.
* **Zero-Code Cloud Migration:** 100% compatible with PostgreSQL / Supabase by swapping the `DATABASE_URL` connection string in `.env`.


* **Data Validation & Serialization**: **Pydantic v2**
* Runtime schema enforcement (`BaseModel`) for all REST payloads, ingestion schemas, WebSocket event frames, and LLM structured JSON generation.


* **Server Execution**: **Uvicorn**
* High-performance ASGI web server worker.



---

## 🧠 2. Artificial Intelligence & LLM Stack

* **Primary Cloud Intelligence**: **Google Gemini API (`google-genai` SDK)**
* **Model**: `gemini-3.6-flash`
* **Ingestion Engine**: Converts raw unstructured resume text and pasted JD text into standardized, strongly-typed JSON objects (`CandidateProfile` & `ParsedJD`).
* **Stage 1 (JD Research & Intelligence Engine)**: Conducts deep structural breakdown of JDs and Tavily web search synthesis to produce **`jd_detail`** (role context, market intelligence, company background).
* **Stage 2 (Question & Prompt Engine)**: Synthesizes candidate match matrices, constructs the 15-question tree, and embeds **`interview_behavior`** (Eva's tone, system prompts, strictness level, and dynamic `whisper_domain_vocabulary`).
* **Stage 4 (Reports Engine)**: 3-branch multimodal evaluation (Audio, Technical Transcript, Combined) with exponential backoff rate-limit handling.


* **Local Neural Brain (Offline LLM Engine)**: **Ollama + Qwen 2.5 (3B)**
* Low-latency streaming response generation during live conversations, dynamically steered using `interview_behavior` and `jd_detail` loaded directly from SQLite.


* **Turn-Taking Classifier (Offline LLM Engine)**: **Ollama + Qwen 2.5 (1.5B)**
* Hybrid conversational turn-taking classifier (Tier 1 Regex + Tier 2 Qwen 1.5B) resolving candidate pauses, hesitation checks, and barge-ins.


* **Speech-to-Text (STT)**: **Faster-Whisper (CTranslate2 / OpenAI Whisper `small` int8)**
* Real-time streaming transcription loaded offline (`HF_HUB_OFFLINE=1`), dynamically boosted with candidate-specific `whisper_domain_vocabulary` extracted from Stage 2 `interview_behavior`.


* **Voice Activity Detection (VAD) & Audio DSP**: **Silero VAD (v3 ONNX Runtime)**
* Speech start/stop detection with dynamic RMS peak auto-gain normalization.
* High-pass IIR filtering (`alpha=0.995`) to remove DC drift before feeding 16kHz PCM audio to Whisper.


* **Text-to-Speech (TTS)**: **Kokoro-82M (PyTorch / KPipeline)**
* High-fidelity neural speech synthesis loaded offline, outputting audio chunks to the persistent streaming buffer under 250ms TTFA (Time-To-First-Audio).



---

## 🎨 3. Presentation Layer & Browser Audio Transport

* **Web Application Client**: **Next.js (React 18/19) + Tailwind CSS**
* Modern web UI for file upload/pasting, setup, question previews, live voice calls, and post-interview analytics dashboards.


* **Browser Audio Engine**: **Web Audio API & AudioWorklet**
* Converts raw browser microphone streams (Opus/WebM) into uniform **16kHz 16-bit Mono PCM bytes** on the client side before streaming across the WebSocket.
* Handles **Barge-In / Interruption Events**: Instantly clears the local Web Audio playback queue when the backend sends an `INTERRUPT` signal.


* **Legacy Desktop Client**: **Kivy 2.3 GUI**
* Standalone Python desktop UI (maintained for local testing).



---

## 🌐 4. Web Intelligence & Scraping Engine

* **Search API**: **Tavily Search API**
* Domain-restricted market intelligence extraction.


* **HTTP Client**: **httpx**
* Asynchronous HTTP requests with connection pooling.


* **HTML Parsing**: **BeautifulSoup4 / lxml**
* Web content extraction from developer portals (LinkedIn, GitHub, StackOverflow, LeetCode, Medium).



---

## 📄 5. Document Ingestion & Parsing Engine

* **Multi-Format Resume Ingestion**:
* **PDF Files (`.pdf`)**: Text and structure extraction via `pypdf`.
* **Word Documents (`.docx`)**: Paragraph and table text extraction via `python-docx`.
* **Plain Text & LaTeX (`.txt`, `.tex`)**: Direct string decoding and clean regex sanitization.


* **LLM Schema Structuring**:
* Parsed raw text from any format is fed into Gemini via Pydantic schema enforcement to extract candidate name, contact, technical skills array, work history, projects, and education into a standard JSON payload.


* **Job Description Conversion**:
* Converts pasted raw text into structured JSON containing role scope, required skills, optional skills, and experience level for downstream Stage 1 & 2 engines.



---

## 🛠️ 6. Development, DevOps & Security Tooling

* **Runtime Environment**: Python 3.12+ (`.venv`)
* **Interactive Batch Script**: `run.bat` (Windows automated launcher for running the FastAPI web server, CLI test harnesses, and quality audits)
* **Code Quality & Security Suite**:
* **Ruff**: Ultra-fast Linter and Code Formatter.
* **Pylint & Mypy**: Static analyzer and strict type checker enforcing Python 3.10+ type safety.
* **Bandit**: Automated security audit scanner identifying AST vulnerability patterns (e.g., hardcoded credentials, unsafe queries).
* **Radon**: Cyclomatic Complexity (`cc`) and Maintainability Index (`mi`) telemetry analyzer.
* **Audit Script**: `scan_code_quality.py` (Master quality scanner).


* **Version Control**: Git & GitHub

```

```

---

## Session Log — 2026-08-07 | Stage 3: Voice-to-Voice Audio Pipeline Fix

### Problem
Listener permanently stuck in "Listening..." state in college environment. Silero VAD reported `prob=0.001` across all 1929 frames in a 62-second session recording — no speech detected despite user actively speaking.

### Root Cause Analysis

**Bug 1 — KMixer Aliasing (Critical)**
`sd.InputStream(samplerate=16000)` succeeded on Realtek MME (44100Hz native) via Windows KMixer, which internally resampled 44100→16kHz using a poor algorithm. The output had energy (RMS 0.01–0.33) but no speech spectral content. VAD ONNX model correctly returned `prob=0.001` — it was genuinely not speech.

Confirmed by running Silero VAD offline against the saved `recording.wav`: `Max VAD prob = 0.0031` across the entire 62-second recording.

**Bug 2 — BargeInWatcher had same aliasing bug**
Both `listen_and_transcribe()` and `BargeInWatcher._watch_loop()` used the Method A/Method B fallback pattern — Method B (16kHz) always won on MME devices.

**Bug 3 — Ollama unavailable → 2.3s per-turn extension**
`turn_classifier.py` Tier 2 timeout was returning `"INCOMPLETE"` when Ollama was unreachable, extending every pause by 2.3s.

### Fixes Applied

| File | Change |
|---|---|
| `listener.py` — `_calibrate_noise_floor()` | Opens at device native rate; collects 30 resampled frames; returns `(floor, noise_spectrum)` tuple |
| `listener.py` — `_spectral_subtract()` | NEW: Per-frame spectral subtraction noise cancellation (FFT, oversubtraction ×2.0, spectral floor 0.2%, IFFT) |
| `listener.py` — `listen_and_transcribe()` | Queries native rate before opening stream; always uses native rate; applies spectral subtraction to `vad_frame` before VAD; persistent `_ratecv_state` for smooth 44100→16kHz interpolation |
| `listener.py` — `BargeInWatcher._watch_loop()` | Same native-rate-first pattern; removed Method A/B fallback |
| `turn_classifier.py` | Added `_probe_ollama_available()` at module load; skips Tier 2 if Ollama unreachable; timeout fallback returns `"COMPLETE"` |
| `.env` | Added `NOISE_FLOOR_OVERRIDE` under Section 5; `MIC_DEVICE_INDEX=1` (Realtek MME) |

### Verification
- `ast.parse()` syntax check: ✅ PASS on all modified files
- WAV forensics: confirmed aliased audio → VAD `prob=0.001` → root cause established
- Spectral subtraction algorithm: mathematically correct, no external dependencies (pure NumPy FFT)