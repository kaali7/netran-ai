# Netran AI — Current System Architecture & Implementation Status

**Status:** ✅ **FULL-STACK OPERATIONAL (Web Client + FastAPI Gateway + Voice AI Engine)**  
**Root Paths:** `backend/` & `frontend/`  
**Last Synchronized:** 2026-08-23

---

## 📌 Executive Summary

Netran AI is a production-grade, multimodal AI technical interviewer platform. The platform is architected into a **React 18 + Vite Web Client**, a high-performance **FastAPI API Gateway**, and **four modular AI pipeline stages** powered by Google Gemini, Faster-Whisper, Silero VAD, Kokoro-82M, and local Ollama neural reasoning.

1. **Web Client (React 18 + Vite):** Serene Learning glassmorphic UI featuring candidate dashboard telemetry, practice track setup, real-time voice interview room with live speech-to-text dialogue stream, animated Eva avatar with acoustic speaking pulse, multimodal scorecard reports, and account settings.
2. **Web API Gateway (FastAPI):** JWT authentication, candidate profile management (`display_name`), bcrypt password changes, DB-backed notification system, template mock interview catalog, session history archive, and analytics telemetry.
3. **Stage 1 (Research Model):** Web-augmented Job Description analysis and Tavily market intelligence search.
4. **Stage 2 (Question Engine):** Candidate resume parsing, skill gap matrix calculation, and 15-question contextual tree generation.
5. **Stage 3 (Voice-to-Voice Loop):** Real-time full-duplex WebSocket voice interaction (VAD + STT + Streaming LLM + Neural TTS) utilizing local Qwen2.5:3B reasoning, Kokoro-82M TTS, and a hybrid turn-taking classifier (Tier 1 Regex + Tier 2 Ollama Qwen2.5:3b).
6. **Stage 4 (Reports Engine):** Non-destructive audio slicing, precision telemetry extraction, and 3-branch Gemini multimodal evaluation.

---

## 📊 Summary Matrix: Subsystem Status

| Subsystem | Module / Directory | Status | Key Technologies & Output Deliverables |
|---|---|---|---|
| **Web Client** | `frontend/` | ✅ **Covered** | React 18, Vite 5, Lucide Icons, Web AudioWorklet, Zustand. 9 Complete Pages (Dashboard, Setup, Interview, Processing, Report, Login, History, Analytics, Settings). |
| **API Gateway** | `backend/api/` | ✅ **Covered** | FastAPI 0.115+, Uvicorn, OAuth2 JWT auth, SQLAlchemy SQLite ORM (`users`, `sessions`, `session_artifacts`, `notifications`), 9 active REST routers + WebSockets. |
| **Stage 1** | `research_model` | ✅ **Covered** | Gemini 3.6 Flash, Tavily API, SQLite caching (`cache.db`). Output: `InterviewRubric` object. |
| **Stage 2** | `question_model` | ✅ **Covered** | Gemini 3.6 Flash, `pypdf`, `python-docx`. Output: `interview_questions.json`, `interviewer_behavior.json`, `resume_analysis.json`. |
| **Stage 3** | `voice_to_voice_model` | ✅ **Covered** | Silero VAD v3 ONNX, Faster-Whisper int8, Ollama Qwen2.5:3b, Kokoro-82M TTS, Hybrid Turn Classifier, AudioWorklet 48k→16k downsampling. Output: `recording.wav`, `transcript.json`. |
| **Stage 4** | `reports_model` | ✅ **Covered** | Audio slicing, Gemini 3-branch evaluation (Audio/Tech/Combined) with 429 RateLimit retry. Output: `report.json`, `evaluation_summary.md`. |
| **Workflow** | `workflow` | ✅ **Covered** | Master pipeline coordinator (`orchestrator.py`), 6-screen Kivy UI (legacy desktop runner). |

---

## 🏗️ System Architecture & End-to-End Workflow

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  React 18 + Vite Web Client (frontend/)                                     │
│  • Dashboard Telemetry, Session History, Performance Analytics              │
│  • Setup Wizard: Dual JD Input (Paste text or File) + Resume Upload         │
│  • Instant Template Picker (Backend, Frontend, Full Stack AI Tracks)        │
│  • Real-Time DB Notifications Dropdown (Unread count, auto-welcome)         │
│  • Profile & Password Settings Management                                   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ REST API / JWT Bearer
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FastAPI Gateway (backend/api/)                                             │
│  • Auth (/signup, /login, /me, /profile, /change-password)                  │
│  • Ingest (/ingest/resume, /ingest/jd)                                      │
│  • Setup & Questions (/setup/analyze, /setup/sessions, /questions/{id})     │
│  • Templates (/template/list, /template/start with dynamic user name)       │
│  • Notifications (/notifications with Stage 2 & 4 automated event triggers) │
│  • History & Analytics (/history/sessions, /analytics/summary)              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│ STAGE 1: Research     │   │ STAGE 2: Question     │   │ STAGE 3: Voice Loop   │
│ • Tavily Web Search   │──▶│ • Skill Gap Matrix    │──▶│ • Full-Duplex WS      │
│ • Gemini Rubric Gen   │   │ • 15-Question Tree    │   │ • Silero VAD + Gain   │
│ • SQLite Hash Cache   │   │ • Eva Behavior Prompt │   │ • Faster-Whisper STT  │
└───────────────────────┘   └───────────────────────┘   │ • Ollama Qwen2.5:3b   │
                                                        │ • Kokoro-82M TTS      │
                                                        │ • Hybrid Classifier   │
                                                        └───────────┬───────────┘
                                                                    │
                                                                    ▼
                                                        ┌───────────────────────┐
                                                        │ STAGE 4: Evaluation   │
                                                        │ • Audio Turn Slicing  │
                                                        │ • 3-Branch Gemini AI  │
                                                        │ • Report & Telemetry  │
                                                        └───────────────────────┘
```

---

## 🔍 Detailed Subsystem Highlights

### 1. Web Client & Interview Room
- **Live Dialogue Transcript Panel**: Real-time turn-by-turn chat modal in `Interview.jsx` displaying Eva questions and candidate transcribed responses with automatic smooth scrolling.
- **Eva Vector Speaking Avatar**: Acoustic glowing ring animation in `AvatarEva.jsx` synchronized with speech synthesis states.
- **Notifications Hub**: DB-backed notification tray in `Navbar.jsx` with unread badges, vector icons, relative timestamps, and one-click report navigation.
- **Candidate Profile & Security**: DB-persisted `display_name` editing and bcrypt password updates in `Settings.jsx`.
- **Pre-Built Mock Interview Catalog**: Instant practice interviews with customized candidate name personalization across system prompts and resume analyses (100% Rule 15 icon compliant).

### 2. Voice Pipeline Timing & Optimization (Aug 2026 Audit)
- **Calibration Cache**: Pre-turn 960ms ambient noise calibration cached across turns to eliminate discarded leading speech.
- **Multi-Hardware Native Rate Handshake**: Voice engine forces physical mic hardware to open at native OS rate (e.g., 44.1kHz or 48kHz) and performs real-time AudioOp downsampling to 16kHz, preventing MME driver silent-channel saturation that breaks Silero VAD on external laptops.
- **Dynamic Threading**: Faster-Whisper CPU threads scale dynamically to `os.cpu_count() - 2` to minimize STT latency on high-core CPUs.
- **Strict Mode Double-Connect Guard**: Global `ACTIVE_WS_CONNECTIONS` lock deduplicates React Strict Mode WS race conditions that previously spawned concurrent conflicting voice engines.
- **Web Pause Tolerance**: Adjusted to 1200ms with 800ms minimum speech frames for conversational naturalness.
- **Whisper Latency Tuning**: `hallucination_silence_threshold` set to 0.5s, eliminating ~2s of trailing silence analysis.
- **Zero Wiener Filter Latency**: `noisereduce` bypassed for WebSocket sessions since browser `getUserMedia` handles noise suppression.
- **Post-TTS Echo Guard**: 600ms guard protects against browser audio playback tail reflections.
- **Native AudioContext**: Browser AudioContext captures native 48kHz audio; `pcm-processor.js` handles explicit downsampling to 16kHz PCM.

### 3. API Gateway & Network Integration
- **Universal LAN CORS**: Fully configured `CORSMiddleware` with `allow_origin_regex` to support cross-origin authenticated testing on mobile devices, local LAN IPs (`192.168.x.x`, `10.x.x.x`), and standard localhost ports (`5173`, `3000`).

---

## 🛠️ Code Quality & Verification Suite

1. **Automated Scanner**: `scan_code_quality.py` audits docstrings, type annotations, and AST security across `backend/`.
2. **Frontend Production Build**: Verified with `npm.cmd run build` inside `frontend/` (0 errors, 1696 modules transformed).
3. **Interactive Batch Launcher**: Master `run.bat` provides comprehensive execution, testing, and database reset/cleaning routines.

---

## 🚀 Future Roadmap (Phase 3)
1. **Admin Evaluation Panel (Feature NF9)**: RBAC-protected candidate assessment matrix.
2. **PostgreSQL / Supabase Migration (Feature NF10)**: Production migration validation for multi-tenant deployments.
