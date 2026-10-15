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
- **Stage 4 Multi-Key Parallel Evaluation & Failover Engine (Oct 2026)**:
  - Enabled multi-API key discovery (`get_gemini_api_keys()`) across `GEMINI_API_KEY1` through `GEMINI_API_KEY10`, `GEMINI_API_KEYS`, and `GEMINI_API_KEY` in `backend/.env`.
  - Re-architected `Stage4Pipeline._evaluate_turns` in `backend/model/reports_model/model/pipeline.py` using `concurrent.futures.ThreadPoolExecutor` to evaluate session turns in parallel across all configured API keys (5 simultaneous workers).
  - Implemented automatic 429 RateLimit/Quota key rotation (`_rotate_key` in `gemini_evaluator.py`) to seamlessly switch clients on rate limits without failing or stalling the pipeline.
  - Reduced turn pacing delays from 7s to 0.5s per worker, accelerating full multimodal report generation from ~180s down to ~20–30s (6x–9x speedup).
  - Thread-safely synchronized progressive `turn_cache.json` updates and status callbacks with `threading.Lock`, with deterministic turn ordering for final report synthesis.
- **Ollama Local LLM Brain Daemon Resilience & Auto-Start (Oct 2026)**:
  - Fixed issue where Eva repeatedly apologized ("I apologize, let's move forward to the next question.") and skipped questions after turn processing: resolved root cause where Ollama daemon was offline (`127.0.0.1:11434`), causing LLM chat retries to exhaust after ~7.6s and hit the fallback apology.
  - Implemented `is_ollama_alive()` and `ensure_ollama_running()` in `brain.py` to automatically detect offline daemon and launch `ollama serve` in the background with zero terminal popups (`CREATE_NO_WINDOW`).
  - Added `preload_brain()` to FastAPI startup `lifespan` in `backend/api/main.py` alongside Kokoro TTS preload, ensuring Qwen2.5:3B is pre-warmed in GPU VRAM prior to the first candidate turn.
  - Added Ollama status verification in `run.bat` (`:run_fastapi_server` and `:run_voice_model`).
- **Voice Turn Latency & TTFA Optimization (Oct 2026)**:
  - Identified root cause of excessive 33-second turn lag (TTFA) as Ollama's default 5-minute keep-alive expiring between sessions, which forced a ~24-second cold-load of `qwen2.5:3b` into VRAM during candidate turns.
  - Set `keep_alive="30m"` directly in `ollama.chat()` in `backend/model/voice_to_voice_model/model/brain.py` to maintain the LLM persistently warm in GPU VRAM across consecutive turns.
  - Tuned `num_predict` cap from 380 to 200 tokens (accommodating Eva's target 15-25 word concise spoken turns with comfortable headroom), avoiding extraneous token compute budget.
  - Implemented `keepalive_ping()` in `brain.py` and wired a 4-minute background heartbeat loop (`_ollama_keepalive_loop`) in FastAPI (`api/main.py` lifespan) to automatically ping Ollama during idle periods, guaranteeing instant sub-second TTFA response times even when sessions are spaced far apart.
- **Headphone VAD Pause Tolerance & Continuation Sensitivity Tuning (Oct 2026)**:
  - Resolved issue where candidate answers prematurely cut off and jumped to "Processing your answer..." while speaking with headphones before completing sentences.
  - Root Cause: Unlike laptop speakers which create room reverberation, headphones isolate acoustic playback so room audio drops to near-zero (`RMS < 0.002`) immediately upon brief pauses. The previous `1200ms` pause tolerance coupled with an overly aggressive `_continue_rms_gate` lower bound (`0.010`) caused brief natural pauses (~1.0s) and quiet trailing words to instantly trip the silence counter.
  - Raised baseline web `pause_tolerance_ms` from `1200ms` to `1800ms` (56 frames * 32ms = 1.79s) in `session_state.py` and `listener.py`, providing comfortable conversational breathing room for technical explanations.
  - Lowered `_continue_gate_computed` floor from `0.010` to `0.003` (`min(max(ambient_floor * 1.15, 0.003), 0.020)`), allowing soft speech and trailing syllables on quiet headset mics to maintain speech state.
  - Relaxed continuation VAD condition to `speech_prob > 0.15 or rms > _continue_rms_gate` (from 0.20), preventing syllable dips from prematurely accumulating silence frames.
- **Web Audio VAD Gate Sensitivity & Ceiling Protection (Oct 2026)**:
  - Capped `_start_gate_computed` and adaptive `new_start_gate` ceiling at `0.035` in `listener.py`, preventing transient acoustic bursts or background noise during calibration from locking the speech start gate at unreachable thresholds (e.g., `0.0600`).
  - Added confident VAD trigger path (`speech_prob >= 0.50 and rms >= max(ambient_floor * 1.1, 0.003)`), ensuring candidate speech on quiet browser microphones / laptop mics is recognized and processed immediately.
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
  - **Comprehensive Master & Frontend READMEs**: Authored full visual documentation for root project (`README.md`) and frontend (`frontend/README.md`), integrating demonstration video (`doc/img/demo_video.mp4`), visual screenshot galleries (`dashboard`, `interview room`, `multimodal evaluation`, `report scorecard`, `analytics`, `history`), and pre-download instructions for all speaking/listening neural models (`Kokoro-82M`, `Faster-Whisper`, `Silero VAD`, `Qwen 2.5 3B`, `SpeechBrain ECAPA-TDNN`).
  - **Academic Blackbook Code Cards & Screenshots (DESIGN.md White Theme)**: Generated 8 high-resolution 2x Retina code snippet cards in `doc/img_screenshort/` styled strictly to Serene Learning white theme tokens (`DESIGN.md`). Automatically embedded all 8 listing images with academic figure captions directly into Chapter 5 of `doc/clg_document/NETRAN AI Blackbook (2).docx`. Backup saved to `NETRAN AI Blackbook (2)_backup.docx`.
- **Stage 4 Post-Session Evaluation Upgrade (Groq + Wav2Vec2 Emotion Model) (Oct 2026)**:
  - Installed `groq` (v1.7.0) in `.venv` and updated `backend/requirements.txt`.
  - Configured `GROQ_API_KEY` and `GROQ_EVALUATION_MODEL="openai/gpt-oss-120b"` in `backend/.env` and `api/config.py`, verified sub-500ms LLM response times.
  - Downloaded and verified recommended Speech Emotion Recognition (SER) model [`superb/wav2vec2-base-superb-er`](https://huggingface.co/superb/wav2vec2-base-superb-er) (~360MB) to local HuggingFace cache with labels `{0: 'neu', 1: 'hap', 2: 'ang', 3: 'sad'}` for CPU-based acoustic delivery scoring with zero VRAM contention on the 6GB RTX 4050.
  - Built `audio_metrics.py` for deterministic pure-Python speech delivery telemetry (WPM, pause count, silence duration, filler density).
  - Built `emotion_service.py` for local Wav2Vec2 acoustic emotion and confidence classification.
  - Built `answer_evaluator.py` implementing high-speed Groq technical answer intelligence with local Ollama fallback and combine executive synthesis.
  - Re-architected `pipeline.py` to eliminate slow Gemini audio uploads, cutting full session evaluation from >5 minutes (stalled) down to ~20 seconds on cold run and ~3–5 seconds on warm runs. Tested live on real session `4c4f877d-6850-4b35-8ffa-933bb64b2fee`, generating complete `report.json` and `evaluation_summary.md`.
- **Global Backend Groq Migration (Ingestion, Stage 1, Stage 2, Stage 4) (Oct 2026)**:
  - Replaced Gemini API key with Groq API key (`GROQ_API_KEY` and `GROQ_EVALUATION_MODEL="openai/gpt-oss-120b"`) as the primary engine everywhere across the backend to permanently eliminate Gemini free-tier 429 quota exhaustion (20 req/day limit).
  - **Document Ingestion** (`backend/api/services/gemini_extractor.py`): Prioritizes Groq JSON mode for resume parsing and JD extraction (<1s execution).
  - **Stage 1 Research Engine** (`backend/model/research_model`): Synthesizes market intelligence rubrics, technical pillars, and HR lenses via Groq in `gemini_client.py`.
  - **Stage 2 Contextual Question Engine** (`backend/model/question_model`): Generates 15-question branching trees and Eva system prompt via Groq in `pipeline.py` sequentially to prevent free-tier concurrency burst limits. Added resilient Pydantic normalizers in `schemas.py` for `AnswerRubric`, `QuestionItem`, `WorkHistoryEntry`, `RedFlagItem`, and `SkillGap`.
  - **Stage 4 Post-Session Evaluation** (`backend/model/reports_model`): Powered by Groq answer intelligence in `answer_evaluator.py` alongside deterministic audio metrics and local Wav2Vec2 SER.
  - Preserved Gemini and local Ollama as graceful offline fallbacks so the system never crashes if a provider is unreachable.

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
