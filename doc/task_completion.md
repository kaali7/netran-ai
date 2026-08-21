# Netran AI — Task Completion & Implementation Tracker

This document tracks completed features, pending roadmap tasks, and known bugs for **Netran AI**.

*Last Updated: 2026-08-19*

---

## 📊 High-Level Component Task Completion Matrix

| Stage / Module | Architecture & Description | Key Files & Endpoints | Status |
|---|---|---|---|
| **Backend Core & Auth** | FastAPI Gateway, OAuth2 + JWT Auth, SQLite ORM Models, Security Utilities, Pydantic v2 Schemas | api/main.py<br>api/db.py<br>api/security.py<br>POST /api/v1/auth/token<br>POST /api/v1/auth/signup | ✅ Completed |
| **Ingestion Engine** | Resume upload & extraction (.pdf, .docx, .txt, .tex), pasted JD text parsing, SHA-256 deduplication cache | api/services/text_extractor.py<br>api/services/gemini_extractor.py<br>POST /api/v1/ingest/resume<br>POST /api/v1/ingest/jd | ✅ Completed |
| **Stage 1: Web Intelligence** | Tavily deep web research synthesis & company tech stack analysis | model/research_model/model/pipeline.py<br>api/services/pipeline_runner.py | ✅ Completed |
| **Stage 2: Question Tree** | 15-question dynamic interview tree generation & Eva interviewer behavior prompt engine | model/question_model/model/pipeline.py<br>POST /api/v1/setup/analyze<br>GET /api/v1/questions/status/{id}<br>GET /api/v1/questions/preview/{id} | ✅ Completed |
| **Stage 3: Live Voice Engine** | Full-duplex WebSocket stream, Silero VAD, Faster-Whisper STT, Qwen 2.5 3B brain, Kokoro 82M TTS, barge-in | model/voice_to_voice_model/model/voice_engine.py<br>api/services/voice_adapter.py<br>api/routers/voice.py<br>WS /api/v1/voice/stream/{session_id} | ✅ Completed |
| **Stage 4: Multimodal Evaluation** | 3-branch audio waveform, technical response, and executive hiring summary generation | model/reports_model/model/pipeline.py<br>api/routers/reports.py<br>POST /api/v1/reports/generate/{id}<br>GET /api/v1/reports/{id} | ✅ Completed |
| **Frontend — Dashboard** | React 18 + Vite 5, Serene Learning Glassmorphism, Navbar, WelcomeBanner, StatsRow, LaunchPractice, LastSessionCard, SessionsTable | frontend/src/pages/Dashboard.jsx | ✅ Completed |
| **Frontend — Setup Page** | Configure Practice Track — live resume/JD upload, pipeline status polling, AnalyzingOverlay, 2-tab bar (Question Bank, Resume & Profile Analysis), Instant Cache Autofill | frontend/src/pages/Setup.jsx<br>frontend/src/hooks/useSetup.js<br>frontend/src/services/sessionService.js | ✅ Completed |
| **Frontend — Interview Room** | Live call screen with AvatarEva, timer, mic visualizer, Web Audio PCM streaming to WebSocket, barge-in, TTS gapless playback | frontend/src/pages/Interview.jsx<br>frontend/src/hooks/useInterviewSession.js<br>frontend/public/pcm-processor.js | ✅ Completed |
| **Frontend — Processing Screen** | Animated glassmorphic loading screen with rotating AI stage messages and live backend progress_message polling | frontend/src/pages/Processing.jsx<br>frontend/src/hooks/useReports.js | ✅ Completed |
| **Frontend — Report Scorecard** | Full multimodal evaluation dashboard — pillar scores, voice telemetry, donut gauge, Q-by-Q accordions, hiring signal badge | frontend/src/pages/Report.jsx | ✅ Completed |
| **Frontend — Auth / Login** | Candidate login + signup, JWT session management, Zustand auth store, public/protected route guards | frontend/src/pages/Login.jsx<br>frontend/src/store/authStore.js<br>frontend/src/services/authService.js | ✅ Completed |
| **Frontend — History Page** | Interview archive with real-time backend telemetry, status filters, question bank inspection drawer, resume analysis, CSV export, & audio player | frontend/src/pages/History.jsx<br>frontend/src/services/historyService.js<br>backend/api/routers/history.py | ✅ Completed |
| **Frontend — Analytics Page** | Composite score dashboard with live skill matrix, score trends, AI synthesis insights, custom glassmorphic date filter, & session comparison chart | frontend/src/pages/Analytics.jsx<br>frontend/src/services/analyticsService.js<br>backend/api/routers/analytics.py | ✅ Completed |
| **Template Mock Interview** | Pre-built mock interviews (Backend, Frontend, Fullstack), READY session creation bypassing Stage 1/2 pipeline | api/routers/template.py<br>components/dashboard/TemplatePicker.jsx<br>services/templateService.js | ✅ Completed |
| **Frontend Web Audio Engine** | AudioWorklet converting browser mic to 16kHz 16-bit Mono PCM for WebSocket streaming | frontend/public/pcm-processor.js | ✅ Completed |
| **Error Boundary** | React ErrorBoundary wrapping router in App.jsx with glassmorphic fallback reload UI | frontend/src/App.jsx<br>frontend/src/components/ui/ErrorBoundary.jsx | ✅ Completed |

---

## 🔴 Priority 1 — Fix First (Bugs & Broken UX)

| # | Task | File(s) | Problem | Status |
|---|---|---|---|---|
| **P1-1** | **Remove hardcoded "AS" user initials** | frontend/src/pages/Interview.jsx | Incorrect user initials in UI | ✅ Completed |
| **P1-2** | **Fix alert() for WebSocket error events** | frontend/src/hooks/useInterviewSession.js | Blocking alerts breaking UX | ✅ Completed |
| **P1-3** | **Fix misleading "Restart" button** | frontend/src/pages/Interview.jsx | Button doesn't actually reset session | ✅ Completed |
| **P1-4** | **Fix wrong copy in Processing screen** | frontend/src/pages/Processing.jsx | Refers to OpenAI instead of Faster-Whisper | ✅ Completed |
| **P1-5** | **Remove hardcoded fallback name 'Soni'** | frontend/src/components/layout/Navbar.jsx | Hardcoded default profile name | ✅ Completed |

---

## 🟠 Priority 2 — Fix Soon (Data Integrity & Real Wiring)

| # | Task | File(s) | Problem | Status |
|---|---|---|---|---|
| **P2-1** | **Replace hardcoded History records** | frontend/src/pages/History.jsx | Fake session records | ✅ Completed |
| **P2-2** | **Wire Analytics page to real data** | frontend/src/services/analyticsService.js | Static analytics data | ✅ Completed |
| **P2-3** | **Fix domain copy in Analytics insights** | frontend/src/services/analyticsService.js | Medical terminology in tech report | ✅ Completed |
| **P2-4** | **Real skill telemetry in StatsRow** | frontend/src/hooks/useDashboard.js | Fabricated skill metrics | ✅ Completed |

---

## 🟡 Priority 3 — Polish & UX Improvements

| # | Task | File(s) | Why It Matters | Status |
|---|---|---|---|---|
| **P3-1** | **Interview Question Progress** | frontend/src/pages/Interview.jsx | Clear navigation feedback | ✅ Completed |
| **P3-2** | **Interview Loading State** | frontend/src/pages/Interview.jsx | Improve perceived latency | ✅ Completed |
| **P3-3** | **Mic permission denied UI** | frontend/src/hooks/useInterviewSession.js | Better error handling | ✅ Completed |
| **P3-4** | **Report "New Practice" CTA** | frontend/src/pages/Report.jsx | Drive user engagement | ✅ Completed |
| **P3-5** | **History audio player** | frontend/src/pages/History.jsx | Essential playback functionality | ✅ Completed |
| **P3-6** | **StatsRow skeleton loaders** | frontend/src/components/dashboard/StatsRow.jsx | Eliminate layout shift on load | ✅ Completed |

---

## 🟢 Priority 4 — New Features

| # | Feature | Target Files | Description | Status |
|---|---|---|---|---|
| **F1** | **Real Analytics Aggregation** | backend/api/routers/analytics.py | API for aggregate score trends | ✅ Completed |
| **F2** | **Audio Recording Download** | backend/api/routers/voice.py | Export interview audio | ✅ Completed |
| **F3** | **Per-Question Timer** | frontend/src/pages/Interview.jsx | Track pacing per segment | ✅ Completed |
| **F4** | **Settings / Profile Page** | frontend/src/pages/Settings.jsx | User preference management | ✅ Completed |
| **F5** | **Notifications Bell** | frontend/src/components/layout/Navbar.jsx | System alerts | ✅ Completed |
| **F6** | **Session Duration Metadata** | backend/api/routers/setup.py | Track interview time usage | ✅ Completed |
| **F7** | **Mobile Responsive Layout** | All frontend pages | Mobile / Tablet scaling | ✅ Completed |
| **F8** | **Export Report as PDF** | frontend/src/pages/Report.jsx | Print and share capability | ✅ Completed |
| **F9** | **Execution Logger Trace** | backend/api/routers/voice.py<br>backend/model/.../execution_logger.py | Trace fine-grained metrics for voice WS pipeline | ✅ Completed |

---

## 🔴 New Active Bugs Found — Codebase Scan 2026-08-19

These are **confirmed bugs** discovered during the full codebase scan. Fix before any new feature work.

| # | Bug | File(s) & Lines | Root Cause | Severity |
|---|---|---|---|---|
| **B1** | **`display_name` accessed but doesn't exist in User schema or DB** | `frontend/src/pages/Report.jsx:42` | `user?.display_name` is read in `Report.jsx` but `UserResponse` Pydantic schema (`api/schemas.py:26-33`) and `User` ORM model (`api/models.py:40-52`) have NO `display_name` column. Always `undefined`, silently falls back. | 🔴 High |
| **B2** | **Settings password change is a pure UI simulation — never hits backend** | `frontend/src/pages/Settings.jsx:56-79` | `handlePasswordSubmit` only calls `setPasswordSuccess(true)` with no API call. No `POST /api/v1/auth/change-password` endpoint exists in `auth.py`. Password change never actually occurs. | 🔴 High |
| **B3** | **Settings profile save only patches localStorage — not persisted to DB** | `frontend/src/pages/Settings.jsx:49-53`<br>`frontend/src/store/authStore.js:49-55` | `handleSaveProfile` calls `updateUser()` which only patches `localStorage`. No backend `PATCH /api/v1/auth/profile` endpoint exists. Display name changes are lost on new device/browser. | 🔴 High |
| **B4** | **Stage 4 session directory path may not match voice engine output path** | `api/routers/voice.py` | `pipeline_runner.py` looks for audio at `BASE_DIR / "data" / "sessions" / session_id` but `api/routers/voice.py` looked in root `sessions/`. Paths aligned and fixed. | ✅ Completed |
| **B5** | **Frontend WS hook is missing handlers for 5 backend-emitted event types** | `frontend/src/hooks/useInterviewSession.js:55-99` | Backend emits `SPEAKING_QUESTION`, `LISTENING_CANDIDATE`, `PROCESSING_RESPONSE`, `EVA_RESPONDING_BRANCH`, `TURN_COMPLETE`. Handlers added to keep UI synced. | ✅ Completed |
| **B6** | **Navbar notifications are hardcoded dummy data — not real-time** | `frontend/src/components/layout/Navbar.jsx:17-42` | Notifications array is 3 hardcoded entries initialized at startup. `markAllRead` only patches local React state. No backend `/api/v1/notifications` endpoint exists. Candidates always see fake placeholder notifications. | 🟠 Medium |
| **B7** | **Template catalog uses raw emoji in `icon` field (Rule 15 violation)** | `api/routers/template.py:41,52,63` | `TEMPLATE_CATALOG` sets `"icon": "⚙️"`, `"🎨"`, `"🤖"` — raw emoji strings returned via `GET /template/list` and potentially rendered directly in `TemplatePicker.jsx`. Violates Rule 15: no raw text emojis in UI design elements. | 🟠 Medium |
| **B8** | **WebSocket Audio Streaming & VAD Sync missing** | `api/routers/voice.py`<br>`model/speaker.py`<br>`useInterviewSession.js` | Backend played audio natively via PyAudio instead of WS streaming. VAD stats were not passed to WS. Rewrote `speaker.py` to support `audio_out_queue`, synced VAD via `AUDIO_LEVEL` event, fixed frontend sample rate to 24kHz. | ✅ Completed |
| **B9** | **React Strict Mode Double-Connect & Kokoro TTS Latency locking voice session** | `api/routers/voice.py`<br>`model/speaker.py`<br>`api/main.py`<br>`useInterviewSession.js` | WebSocket double connect locked room to EVALUATING; Kokoro TTS lazy loading (15s) caused timeouts before audio. Fixed via lifespan preload & state checks. | ✅ Completed |
| **B10**| **No Audio via WebSocket due to Global Player Overwrite & Logger Path Error** | `api/routers/voice.py`<br>`model/speaker.py`<br>`model/voice_engine.py`<br>`model/execution_logger.py` | Strict Mode double connect overwrote global `_default_player` queues. `float64` array volume boost caused 2x TTS playback slowdown. `ExecutionLogger` path mapped to wrong dir. Instantiated local `PersistentSpeaker` per-session. | ✅ Completed |
| **B11**| **React 18 Strict Mode `ws.onclose` Race Condition Aborting Active WebSocket** | `frontend/src/hooks/useInterviewSession.js` | On Strict Mode double-mount, old WebSocket instance `ws1` finished closing and fired `onclose`, which invoked `stopSession()`. This accidentally killed the active `ws2` instance (`wsRef.current`). Fixed with instance equality guard. | ✅ Completed |
| **B12**| **Engine Turn 0 Blocking Execution Loop** | `model/voice_to_voice_model/model/voice_engine.py` | Synchronous `speak_text(initial_greeting)` blocked the main engine thread during audio generation, delaying the `while not stop_event.is_set()` loop. Fixed by dispatching greeting in background thread. | ✅ Completed |
| **B13**| **`CandidateReportPayload` Schema Attribute Mismatch in Pipeline Runner** | `backend/api/services/pipeline_runner.py` | Stage 4 execution logging attempted to access `final_report.overall_score` instead of `overall_technical_score`, raising an `AttributeError` that rolled back the DB transaction and kept sessions in `EVALUATING` state forever. | ✅ Completed |
| **B14**| **Web Audio 20x Pre-Gain Locking VAD Continuation Gate & Prolonging Silence Delays** | `backend/model/voice_to_voice_model/model/listener.py` | Hardcoded 20x gain applied to normalized Web Audio amplified room noise/breathing by 2000%, locking the continuation gate for 30–54s per turn. Differentiated pre-gain (1.0x for Web Audio, 20.0x for desktop mic). | ✅ Completed |
| **B15**| **Missing `mic_writer` in Voice Engine Resulting in Empty 44-Byte `continuous_mic_input.wav`** | `backend/model/voice_to_voice_model/model/voice_engine.py` | `mic_writer` was instantiated but omitted from `listen_and_transcribe()` call, causing 0 frames to be recorded and failing Stage 4 audio slicing. Added `mic_writer=mic_writer`. | ✅ Completed |
| **B16**| **Inactive `SpeakerVerifier` (ECAPA-TDNN) in Live Web Interview Engine** | `backend/model/voice_to_voice_model/model/voice_engine.py` | `SpeakerVerifier` was never instantiated in `WorkflowVoiceEngine`. Initialized verifier and passed to `listen_and_transcribe()` for candidate identity verification and background voice rejection. | ✅ Completed |
| **B17**| **Frontend Card Shaking & Height Jitter on Eva Speaking State Toggle** | `frontend/src/pages/Interview.jsx` | Conditional DOM mounting (`{!isSpeaking && <MicLevelBar />}`) altered card height by 42px on every turn, causing visible page shaking. Replaced with fixed-height slot and smooth opacity transitions. | ✅ Completed |
| **B18**| **Candidate Nervousness & Stop Phrases Unhandled Leading to Premature Question Advance** | `question_manager.py`<br>`voice_engine.py` | Phrases like `"can stop this interview i feel nervous"` missed rigid substring checks. Expanded intent regex and formatted empathetic reassurance closing without pivoting to next question. | ✅ Completed |
| **B19**| **Speaker Verifier False Rejections Trapping Candidate in 30s Silent Loop** | `speaker_verifier.py`<br>`listener.py` | Strict `0.55` threshold falsely rejected candidate utterances, silently resetting the audio buffer into a 30s wait loop. Lowered threshold to `0.30` and implemented fail-open fallback. | ✅ Completed |
| **B20**| **Mouth Movement & Question Text Prematurely Triggering 3s Before TTS Audio Arrival** | `frontend/src/hooks/useInterviewSession.js` | JSON metadata events prematurely triggered `isSpeaking` and question updates while TTS was still synthesizing. Re-anchored `isSpeaking` and question switch strictly to Web Audio playback with a 180ms anti-flutter debounce. | ✅ Completed |
| **B21**| **VAD Status Pill Under Avatar Vibrating Due to 30fps Floating-Point Text Length Changes** | `frontend/src/pages/Interview.jsx` | Rapid numerical stream text (`VAD: 0.12 RMS: 0.0034`) caused dynamic pill width oscillation. Sanitized to stable fixed labels (`Listening`, `Hearing you...`, `Processing answer...`, `Eva is Speaking`) with `minWidth: 190px`. | ✅ Completed |

---

## 🔵 Pending New Features & Improvements — Roadmap 2026

Items identified from the codebase scan that are not yet built.

| # | Feature | Target Files | Description | Priority |
|---|---|---|---|---|
| **NF1** | **User Profile Update Endpoint + `display_name` Column** | `api/routers/auth.py` (new endpoint)<br>`api/models.py` (add `display_name`)<br>`api/schemas.py` (add `display_name` to `UserResponse`) | Add `display_name` DB column. Create `PATCH /api/v1/auth/profile` endpoint. Wire to `Settings.jsx`. Fixes B1 & B3. | 🔴 High |
| **NF2** | **Password Change Endpoint** | `api/routers/auth.py` (new endpoint)<br>`api/security.py` | Create `POST /api/v1/auth/change-password` with `{current_password, new_password}` bcrypt verification & update. Wire to `Settings.jsx`. Fixes B2. | 🔴 High |
| **NF3** | **Session Directory Path Alignment (Stage 4 Audio)** | `api/routers/voice.py` | Trace and verify `WorkflowVoiceEngine` saves `recording.wav` to same directory `run_stage4()` reads from. Paths aligned in `voice.py`. Fixes B4. | ✅ Completed |
| **NF4** | **Wire Missing WS Event Handlers in Interview Room** | `frontend/src/hooks/useInterviewSession.js` | Add handlers for `SPEAKING_QUESTION`, `LISTENING_CANDIDATE`, `TURN_COMPLETE`, `PROCESSING_RESPONSE`, `EVA_RESPONDING_BRANCH`. Map to `isSpeaking`, `currentQuestion`, UI state transitions. Fixes B5. | ✅ Completed |
| **NF5** | **Replace Template Emoji Icon Field with String Identifiers** | `api/routers/template.py:41,52,63`<br>`frontend/src/components/dashboard/TemplatePicker.jsx` | Replace `"⚙️"`, `"🎨"`, `"🤖"` with string labels (e.g. `"server"`, `"layout"`, `"cpu"`) and render Lucide SVG icons in `TemplatePicker.jsx`. Fixes B7. | 🟠 Medium |
| **NF6** | **Real-Time Notifications System** | `api/routers/` (new `notifications.py`)<br>`api/models.py` (new `Notification` table)<br>`frontend/src/services/notificationsService.js`<br>`frontend/src/components/layout/Navbar.jsx` | Replace hardcoded Navbar notifications with real DB-backed system events (session ready, evaluation complete, pipeline error). Fixes B6. | 🟠 Medium |
| **NF7** | **Live Transcript Display in Interview Room** | `frontend/src/pages/Interview.jsx` | Pipe `candidate_transcript` from `EVA_RESPONDING_BRANCH` WS events into a scrolling live transcript panel in the Interview Room UI. | 🟡 Medium |
| **NF8** | **Eva Speaking Indicator Enhancement** | `frontend/src/pages/Interview.jsx`<br>`frontend/src/components/interview/AvatarEva.jsx` | Tie `SPEAKING_QUESTION` / `AI_STOP_SPEAKING` events precisely to AvatarEva pulse animation and "Eva is speaking..." label. Currently `isSpeaking` relies on binary blob messages which may lag. | 🟡 Medium |
| **NF9** | **Admin Evaluation Panel** | `api/routers/` (new `admin.py`) | RBAC-protected admin dashboard to access all candidate sessions, scores, and reports. Currently only candidate RBAC exists. | 🟢 Low |
| **NF10** | **PostgreSQL Migration Validation** | `api/config.py` · `api/db.py` | Swap `DATABASE_URL` from SQLite to PostgreSQL/Supabase and validate full migration path including auto-schema creation. | 🟢 Low |

---

## ✅ Quality Assurance & Verification Log

- ✅ **Database & Schema**: SQLite multi-thread compatibility & auto-migration verified.
- ✅ **Stage 1-4 Pipelines**: All pipelines, status checkpoints, and evaluation artifacts verified.
- ✅ **Frontend Build**: Production build successful (0 errors, 1,695 modules).
- ✅ **Responsive UI**: Full `ui-ux-pro-max` compliance for desktop, tablet, and mobile.
- ✅ **Audio/Visuals**: Waveform visualization, PCM streaming, and interactive playback confirmed.
- ✅ **Execution Tracing**: Comprehensive logging of STT, TTFT, TTS and Audio blob sizes tracing implemented.
- ✅ **Git Integrity**: All major features pushed with clear hash-tagged commit notes.
- 🔴 **Codebase Audit 2026-08-19**: Full scan complete. 7 new active bugs found (B1–B7), 10 pending improvements identified (NF1–NF10). See sections above.

---

## 📋 Known Technical Debt

| Item | Notes |
|---|---|
| PostgreSQL Migration | DATABASE_URL swap from SQLite to PostgreSQL/Supabase not yet production-validated (see NF10) |
| Admin Evaluation View | RBAC-protected admin endpoints not yet built (see NF9) |
| Settings Backend Wiring | `display_name` + password change endpoints missing — Settings is UI-only simulation (see B2, B3, NF1, NF2) |
| Notifications Real-Time | Navbar notifications are hardcoded dummy data, no backend system (see B6, NF6) |
| WS Event Handler Coverage | `useInterviewSession.js` handles documented WS event types |
| Session Dir Path Alignment | Stage 4 audio paths aligned across voice engine and router |
| Template Catalog Emoji Icons | `template.py` TEMPLATE_CATALOG uses raw emojis violating Rule 15 (see B7, NF5) |
