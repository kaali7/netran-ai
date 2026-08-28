# Netran AI — Task Completion & Implementation Tracker

This document tracks completed features, pending roadmap tasks, and known bugs for **Netran AI**.

*Last Updated: 2026-08-23*


---

## 🟢 Completed Tasks & Features

*A consolidated summary of all completed backend, frontend, and integration tasks.*

### Core Systems & Pipelines
- **Backend & Auth**: FastAPI Gateway, JWT Auth, SQLite ORM, Ingestion Engine (Resume/JD), Profile (`display_name`) persistence & verification, password change with bcrypt.
- **Notifications System**: DB-backed `Notification` ORM table, REST API (`/api/v1/notifications`), auto-triggers on Stage 2 setup initialization & Stage 4 post-session evaluation completion.
- **Stage 1 (Web Intelligence)**: Tavily deep web research synthesis.
- **Stage 2 (Question Tree)**: Dynamic interview tree generation & Eva interviewer behavior prompt engine.
- **Stage 3 (Live Voice Engine)**: Full-duplex WebSocket stream, Silero VAD, Faster-Whisper STT, Kokoro TTS.
- **Stage 4 (Multimodal Evaluation)**: Audio waveform, technical response, and executive summary generation.

### Frontend Components & Pages
- **Pages**: Dashboard, Setup, Interview Room, Processing Screen, Report Scorecard, Auth/Login, History, Analytics, Settings.
- **Navbar Real-Time Notifications**: Live DB alerts with unread badge counter, dynamic type icons, formatted relative timestamps, mark all as read, and direct report link navigation.
- **Live Interview Transcript Panel**: Real-time turn-by-turn chat stream displaying Eva questions and transcribed candidate responses with auto-scrolling dialogue bubbles.
- **Enhanced Eva Speaking Avatar**: Acoustic glowing pulse ring animation synchronized with Web Audio playback and voice synthesis states.
- **Settings & Profile Management**: Real DB-backed profile editing (`PATCH /api/v1/auth/profile`) and credential updates (`POST /api/v1/auth/change-password`).
- **Template Mock Interviews (Rule 15 Compliant)**: Replaced raw emojis with string identifiers (`server`, `palette`, `bot`), Lucide vector icons, and dynamic candidate profile name personalization.
- **Web Audio Engine**: Browser mic to 16kHz PCM for WebSocket streaming.
- **UI/UX Refinements**: Mobile responsiveness, glassmorphic themes, interactive audio players, dashboard KPI telemetry, and error boundaries.

### Resolved Bugs & Enhancements
- **Bug B1 & B3 / Feature NF1**: Added `display_name` to DB model, schemas, and `PATCH /auth/profile`. Wired to Settings and Navbar.
- **Bug B2 / Feature NF2**: Implemented `POST /auth/change-password` with bcrypt verification and connected to Settings.
- **Bug B6 / Feature NF6**: Built full DB-backed notifications system and wired to Navbar bell.
- **Bug B7 / Feature NF5**: Replaced template catalog emojis with string identifiers (Rule 15 compliance).
- **Feature NF7 & NF8**: Added Live Interview Transcript modal and Eva speaking pulse animation.
- Fixed WebSocket audio streaming, VAD sync, and React Strict Mode double-connect issues.
- Fixed TTS latency, audio playback overlapping, and mic permission handling.
- Implemented real data wiring for History and Analytics pages.
- Addressed various UI jitter, overflow, and styling issues across mobile and desktop viewports.
- Added session deletion, audio download, and contextual resume actions.
- **Documentation Sync (Aug 2026)**: Scanned full codebase and synchronized all core documentation files (`current.md`, `backend_plan.md`, `frontend_structure.md`, `tech_stack.md`, `folder_strucuture.md`, `rule.md`) to reflect Tri-Mode Execution Architecture (Web, GUI, CLI) and database refinements.
- **Voice Pipeline Timing Audit (Aug 2026)**: Full end-to-end scan of voice flow identified and resolved 7 root causes for inconsistent Eva response timing:
  - **Fix A** (`listener.py` + `session_state.py`): Per-turn 960ms calibration cached across turns — eliminates ~960ms of leading speech being discarded on turns 2+.
  - **Fix B** (`session_state.py` + `listener.py`): `pause_tolerance_ms` raised from 800ms → 1200ms; `MIN_SPEECH_FRAMES` raised from 15 → 25 (800ms min) for web mode.
  - **Fix C** (`listener.py`): `noisereduce` disabled for WebSocket sessions (browser already handles suppression via `getUserMedia`) — saves 500–1500ms per turn.
  - **Fix D** (`listener.py`): Whisper `hallucination_silence_threshold` lowered from 2.0 → 0.5 — saves ~2s per turn.
  - **Fix E** (`listener.py`): Post-TTS echo guard extended from 300ms → 600ms for WebSocket mode — stops Eva's trailing audio re-triggering VAD.
  - **Fix F** (`api/routers/voice.py`): Replaced `get_nowait()` + 20ms sleep polling in `audio_send_worker` with blocking `run_in_executor` — eliminates systematic 20ms chunk jitter.
  - **Fix G** (`pcm-processor.js` + `useInterviewSession.js`): Removed forced `sampleRate: 16000` from AudioContext; worklet now downsamples explicitly from native OS rate (48kHz→16kHz) — eliminates OS resampling artifacts causing false VAD triggers.
- **Cross-Origin Resource Sharing (CORS) & LAN Support (Aug 2026)**:
  - Configured `CORSMiddleware` in `api/main.py` with `allow_origin_regex` to support seamless cross-origin requests from any LAN IP (`192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`), localhost ports (`5173`, `5174`, `3000`), and configurable `API_CORS_ORIGINS`.
  - Added full credentials support (`allow_credentials=True`) for authorization tokens and cookie handshakes across mobile and local network testing.
- **Multi-Hardware Audio & Voice Engine Optimization (Aug 2026)**:
  - Enhanced `listener.py` to always open audio input streams at the physical device's native rate (e.g. 44.1kHz / 48kHz) and perform real-time downsampling, resolving MME driver silent-channel saturation.
  - Dynamically scaled Faster-Whisper CPU threads to available cores (`os.cpu_count() - 2`, up to 8 threads), cutting STT processing latency.
  - Added `NOISE_FLOOR_OVERRIDE` and adaptive `_continue_rms_gate` headroom (2.8x for web sessions) to handle noisy hardware environments.
- **Level 2 TurnManager & Playback Synchronization Architecture (Aug 2026)**:
  - **TurnManager State Machine** (`model/voice_to_voice_model/model/turn_manager.py`): Explicit `ConversationState` machine decoupling raw VAD probabilities from state transitions (`READY`, `EVA_SPEAKING`, `PLAYBACK_ACTIVE`, `ECHO_GUARD`, `LISTENING`, `CANDIDATE_SPEAKING`, `THINKING`).
  - **Browser Playback Synchronization** (`useInterviewSession.js` & `voice.py`): Replaced static 600ms backend guess timer with real Web Audio API `playback_started` and `playback_finished` WebSocket events, ensuring zero false VAD triggers across any laptop.
  - **Pre-Roll Echo Gating & Adaptive Calibration** (`listener.py`): Pre-speech buffer is cleared during non-listening states to prevent Eva acoustic reflections from prepending to speech; dynamic calibration refines `cached_start_rms_gate` per microphone sensitivity.
  - **TurnManager State Lock & Short Answer Filter Fix**: Resolved conversational deadlocks where empty/rejected transcripts left `TurnManager` in `THINKING` state, and expanded `is_valid_transcript` whitelist to correctly accept natural single-word answers ("fine", "good", "ready", "yes", "okay").
  - **Adaptive Calibration Scope & `import re` Fix**: Fixed `UnboundLocalError: ambient_floor` and `NameError: re` in `listener.py` that caused the voice engine to terminate prematurely into Stage 4 evaluation after the candidate's first answer.
  - **VAD Energy Gating & Intent Refinement**: Enforced minimum RMS energy gate (`max(_start_rms_gate * 0.70, 0.006)`) on strong VAD paths in `listener.py` to prevent phantom speech triggers from ambient room murmurs, and refined `stop_pattern` in `question_manager.py` to prevent casual words from prematurely concluding interviews.
  - **Comprehensive Master & Frontend READMEs**: Authored full visual documentation for root project (`README.md`) and frontend (`frontend/README.md`), integrating demonstration video (`doc/img/demo_video.mp4`) and visual screenshot galleries (`dashboard`, `interview room`, `multimodal evaluation`, `report scorecard`, `analytics`, `history`).

---

## 🔴 Pending Tasks & Known Issues

*Active bugs and planned features that require attention.*

### Low Priority (Architecture & Admin)
- **Feature NF9**: Admin Evaluation Panel (RBAC-protected dashboard for all candidate sessions).
- **Feature NF10**: PostgreSQL Migration Validation (Swap SQLite for PostgreSQL/Supabase).

---

## ✅ Quality Assurance Log
- **Database & Schema**: SQLite multi-thread compatibility & auto-migration verified (`display_name` and `notifications` table verified).
- **Pipelines**: All Stage 1-4 pipelines and artifacts verified.
- **Frontend Build**: Production build verification passed (`✓ built in 2.17s`, 0 errors).
- **Backend Syntax**: `listener.py`, `session_state.py`, `api/routers/voice.py` — all pass `python -m py_compile` with exit code 0.
- **Responsive UI**: Desktop, tablet, and mobile compliance verified.
- **Voice Timing (Aug 2026)**: 7-fix pipeline audit applied. Target response gap: 0.8s–2.0s consistent.

## 📋 Known Technical Debt
- PostgreSQL migration not yet production-validated.
- Admin evaluation endpoints missing.
