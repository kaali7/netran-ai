# Netran AI — Technical Stack Architecture

This document defines the complete technology stack powering **Netran AI**, an autonomous, real-time AI-powered technical interviewer platform.

---

## 🏗️ Core Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    React 18 + Vite 5 Web Client (SPA)                       │
│        (Manrope Font, Vanilla CSS Tokens, Lucide Icons, AudioWorklet)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP REST (JSON) / WebSockets (16kHz PCM)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Web API Gateway                              │
│         (Python 3.12 + Uvicorn + OAuth2 JWT + Smart SQLite Caching)         │
└──────┬───────────────┬───────────────┬───────────────┬───────────────┬──────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│ Auth, Profile││  Ingestion   ││ Stage 1 & 2  ││   Stage 3:   ││   Stage 4:   │
│ & Notification││ Engine (Resume││ Research &   ││ Live Voice   ││ Multimodal   │
│ (Bcrypt/JWT) ││ & JD Parsing)││ Question Tree││  (Local GPU) ││ Evaluation   │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

---

## ⚡ 1. Backend Service & API Layer

* **API Web Framework**: **FastAPI (0.115+)**
  * Asynchronous Python web framework built on **Starlette** and **ASGI** (`uvicorn`).
  * OpenAPI documentation automatically generated at `/docs`.
  * Asynchronous background execution (`fastapi.BackgroundTasks`) for Stage 1, 2, and 4 pipelines.
  * Real-time, full-duplex streaming communication over **WebSockets** (`/api/v1/voice/stream/{session_id}`).
  * `CORSMiddleware` with configurable origin whitelist via `API_CORS_ORIGINS`.

* **Ingestion & Data Normalization Endpoints**:
  * **Resume Upload (`POST /api/v1/ingest/resume`)**: Accepts `multipart/form-data` uploads (`.pdf`, `.docx`, `.txt`), parses via `pypdf`/`python-docx`, and extracts structured schemas via Gemini.
  * **JD Text Ingestion (`POST /api/v1/ingest/jd`)**: Accepts pasted raw JD text, extracting core competencies and seniority levels.

* **Authentication, Profile & Security**: **OAuth2 + JWT**
  * Password hashing and verification using `passlib[bcrypt]`.
  * Candidate profile management (`PATCH /api/v1/auth/profile`) for display names.
  * Secure password change with verification (`POST /api/v1/auth/change-password`).
  * Query-parameter authentication support (`?token=...`) for native browser WebSocket handshakes.

* **Notifications Subsystem**:
  * Persistent `Notification` ORM model storing title, message, category, link, and read status.
  * Automated event triggers during Stage 2 initialization and Stage 4 evaluation report completion.
  * REST endpoints for listing, reading, and clearing alerts (`/api/v1/notifications`).

* **Data Persistence & Smart Caching**: **SQLAlchemy + SQLite 3**
  * Storage for users, sessions, artifacts, and notifications with native JSON column support.
  * Input-hash deduplication (SHA-256 fingerprinting) skipping redundant pipeline executions.
  * Zero-code cloud migration path to PostgreSQL / Supabase via `DATABASE_URL`.

---

## 🧠 2. Artificial Intelligence & LLM Stack

* **Primary Cloud Intelligence**: **Google Gemini API (`google-genai` SDK)**
  * **Model**: `gemini-3.6-flash`
  * **Ingestion**: Converts unstructured text into typed schemas (`CandidateProfile` & `ParsedJD`).
  * **Stage 1 (Research)**: Synthesizes web intelligence into structured rubrics (`InterviewRubric`).
  * **Stage 2 (Question Tree)**: Builds 15-question trees and Eva interviewer behavior prompts.
  * **Stage 4 (Evaluation)**: 3-branch multimodal evaluation (Audio, Technical, Combined).

* **Local Neural Brain (Offline LLM Engine)**: **Ollama + Qwen 2.5 (3B)**
  * Low-latency response generation during live interviews, steered by `interviewer_behavior.json`.
  * Persistent `keep_alive="30m"` VRAM caching and automated 4-minute FastAPI background heartbeat to eliminate cold-reload latency spikes.

* **Turn-Taking Classifier (Offline LLM Engine)**: **Ollama + Qwen 2.5 (3B)**
  * Hybrid turn-taking classifier (Tier 1 Regex + Tier 2 Qwen 3B probe) resolving candidate pauses.

* **Speech-to-Text (STT)**: **Faster-Whisper (CTranslate2 `small` int8)**
  * Real-time transcription loaded offline (`HF_HUB_OFFLINE=1`), boosted with domain vocabulary.
  * Tuned with `hallucination_silence_threshold=0.5` to eliminate trailing silence latency.

* **Speaker Verification**: **SpeechBrain ECAPA-TDNN**
  * Auto-enrolls candidate voice print (first utterance >= 2s) and verifies identity (threshold 0.55).

* **Voice Activity Detection (VAD) & DSP**: **Silero VAD (v3 ONNX)**
  * Ambient noise floor calibration cached across turns with dynamic speech level adaptation.
  * 1800ms pause tolerance in web mode (optimized for headphones & natural pauses), dynamic post-playback echo guard, and streaming IIR DC blocking.

* **Conversation Turn Manager & Playback Sync**: **TurnManager State Machine**
  * Decouples raw VAD probabilities from conversational state transitions (`READY`, `EVA_SPEAKING`, `PLAYBACK_ACTIVE`, `ECHO_GUARD`, `LISTENING`, `CANDIDATE_SPEAKING`, `THINKING`).
  * Event-driven client synchronization (`playback_started` / `playback_finished` events from browser Web Audio API).
  * Real-time latency breakdown telemetry and cross-device audio diagnostics.

* **Text-to-Speech (TTS)**: **Kokoro-82M (PyTorch / KPipeline)**
  * Neural speech synthesis with sub-250ms Time-To-First-Audio (TTFA).

---

## 🎨 3. Presentation Layer & Browser Audio Transport

* **Web Application Client**: **React 18 + Vite 5 (SPA)**
  * Serene Learning Modern Glassmorphism design system (Manrope typography, custom CSS tokens).
  * 100% Vector Icon Standard (`lucide-react`) adhering strictly to Rule 15.
  * 9 comprehensive page surfaces: Dashboard, Setup, Interview Room, Processing, Report Scorecard, History, Analytics, Settings, Login.

* **Browser Audio Engine**: **Web Audio API & AudioWorklet**
  * `pcm-processor.js` worklet downsamples native browser audio (48kHz) to 16kHz 16-bit Mono PCM.
  * Handles barge-in interruption events by immediately flushing local audio buffers.

* **Legacy Desktop Client**: **Kivy 2.3 GUI**
  * Standalone desktop test client maintained in `model/workflow/`.

---

## 🌐 4. Web Intelligence & Scraping Engine

* **Search API**: **Tavily Search API**
  * Domain-restricted market intelligence extraction for company context and tech rubrics.
* **HTTP Client**: **httpx**
  * Asynchronous HTTP requests with connection pooling.
* **HTML Parsing**: **BeautifulSoup4 / lxml**
  * Web content extraction from verified technical domains.

---

## 🛠️ 5. Development, DevOps & Security Tooling

* **Runtime Environment**: Python 3.12+ (`.venv`) & Node.js 18+
* **Master Batch Launcher**: `run.bat` (Windows automated launcher for servers, diagnostic tests, DB reset, and cleanups).
* **Code Quality & Security Suite**:
  * **Ruff & Pylint**: Linting and style enforcement.
  * **Bandit**: AST security vulnerability analysis.
  * **Radon**: Cyclomatic complexity and maintainability index telemetry.
  * **Audit Script**: `scan_code_quality.py`.
* **Version Control**: Git & GitHub