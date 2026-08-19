# Netran AI — Task Completion & Implementation Tracker

This document tracks completed features, pending roadmap tasks, and known bugs for **Netran AI**.

*Last Updated: 2026-08-18*

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
| **Frontend — History Page** | Interview archive with search, date/track filters, sessions table, audio recording player modal, View Report nav | frontend/src/pages/History.jsx | ✅ Completed (mock data fallback) |
| **Frontend — Analytics Page** | Composite score dashboard with skill matrix bars and session comparison chart | frontend/src/pages/Analytics.jsx<br>frontend/src/services/analyticsService.js | ⚠️ Hardcoded data — needs real backend |
| **Template Mock Interview** | Pre-built mock interviews (Backend, Frontend, Fullstack), READY session creation bypassing Stage 1/2 pipeline | api/routers/template.py<br>components/dashboard/TemplatePicker.jsx<br>services/templateService.js | ✅ Completed |
| **Frontend Web Audio Engine** | AudioWorklet converting browser mic to 16kHz 16-bit Mono PCM for WebSocket streaming | frontend/public/pcm-processor.js | ✅ Completed |
| **Error Boundary** | React ErrorBoundary wrapping router in App.jsx with glassmorphic fallback reload UI | frontend/src/App.jsx<br>frontend/src/components/ui/ErrorBoundary.jsx | ✅ Completed |

---

## 🔴 Priority 1 — Fix First (Bugs & Broken UX)

These are confirmed bugs found from codebase scan. Fix these before doing any new feature work.

| # | Task | File(s) | Problem | Status |
|---|---|---|---|---|
| **P1-1** | **Remove hardcoded "AS" user initials in Interview Room** | frontend/src/pages/Interview.jsx:149 | User profile initials bubble shows hardcoded "AS" — every user sees wrong initials | ✅ Completed (reads `user?.email` initial via `useAuth()`) |
| **P1-2** | **Fix alert() for WebSocket error events** | frontend/src/hooks/useInterviewSession.js:80 | alert() mid-interview is jarring, blocks the page thread, and breaks the glassmorphic UX | ✅ Completed (replaced with reactive error state + inline glassmorphic banner in `Interview.jsx`) |
| **P1-3** | **Fix misleading "Restart" button in Interview Room** | frontend/src/pages/Interview.jsx:64-66 | handleRestart() only resets the timer display — it does NOT restart the session, question, or WebSocket. Deeply misleading for users | ✅ Completed (renamed to "Reset Timer" with tooltip clarification) |
| **P1-4** | **Fix wrong copy in Processing screen** | frontend/src/pages/Processing.jsx:28 | Message says "Cross-verifying candidate responses against OpenAI Whisper logs..." — the project uses Faster-Whisper locally, NOT OpenAI | ✅ Completed (updated string to "Cross-verifying transcripts via local Faster-Whisper STT logs...") |
| **P1-5** | **Remove hardcoded fallback name 'Soni' in Navbar** | frontend/src/components/layout/Navbar.jsx:16 | Non-user-specific hardcoded name appears as display name if email not loaded | ✅ Completed (replaced with generic 'Candidate' fallback) |

---

## 🟠 Priority 2 — Fix Soon (Data Integrity & Real Wiring)

| # | Task | File(s) | Problem | Fix Needed |
|---|---|---|---|---|
| **P2-1** | **Replace hardcoded fallback mock records in History page** | frontend/src/pages/History.jsx:35-95 | defaultHistoryRecords array with fake sessions (fake dates/scores) shows up when backend is empty | Replace with a clean empty-state component ("No sessions yet" CTA) — no fake records |
| **P2-2** | **Wire Analytics page to real session data** | frontend/src/services/analyticsService.js | Skill matrix, insights, and session comparison data are all static hardcoded fiction. Backend /setup/sessions is called but only used for totalSessions count — rest is fabricated | Build real analytics aggregation from evaluation reports via GET /api/v1/reports/{id} or add dedicated analytics endpoint |
| **P2-3** | **Fix wrong domain copy in Analytics insights** | frontend/src/services/analyticsService.js:33,38,43 | Insights mention "clinical histories", "shared decision-making", "non-verbal cues" — medical interview domain copy, wrong for software tech interview platform | Rewrite insights to reflect tech interview pillars: System Design, Coding Clarity, Problem Decomposition, Communication |
| **P2-4** | **Real skill telemetry in Dashboard StatsRow** | frontend/src/hooks/useDashboard.js:76-87 | strongestSkills and needsFocusSkill return hardcoded text even when completed sessions exist — never reads real report data | Pull from latest session's report.pillar_scores via the Reports API to compute real strongest/weakest domain |

---

## 🟡 Priority 3 — Polish & UX Improvements (Solve After Bugs Are Fixed)

| # | Task | File(s) | Why It Matters |
|---|---|---|---|
| **P3-1** | **Interview Room — show question number progress** | frontend/src/pages/Interview.jsx | questionIndex state is tracked in useInterviewSession.js but never rendered in the UI. A "Q 3 / 10" counter in the header would dramatically improve session awareness |
| **P3-2** | **Interview Room — connection loading state** | frontend/src/pages/Interview.jsx | Between page load and WebSocket onopen, currentQuestion shows "Initializing interview session..." with no spinner or loading skeleton — looks broken | Add a connecting skeleton/spinner overlay for the initial connection phase |
| **P3-3** | **Interview Room — mic permission denied UI** | frontend/src/hooks/useInterviewSession.js:160-162 | getUserMedia errors are silently console.error'd with no user-facing feedback | Catch NotAllowedError and show a styled alert card instructing the user to grant mic access |
| **P3-4** | **Report Page — "New Practice" CTA** | frontend/src/pages/Report.jsx | The report page shows an evaluation but has no prominent "Start Another Session" or "Back to Dashboard" action after reviewing feedback — user journey dead-ends | Add a prominent CTA button row at the bottom of the Report page |
| **P3-5** | **History Page — wire real audio player** | frontend/src/pages/History.jsx | Audio recording modal UI exists but plays nothing — backend recording.wav path is not fetched or streamed to the browser | Wire to GET /api/v1/voice/recording/{session_id} (needs backend endpoint) or expose static file URL |
| **P3-6** | **Dashboard StatsRow — skeleton loaders** | frontend/src/components/dashboard/StatsRow.jsx | Stats cards render with 0 or empty values during the API fetch with no loading skeleton — causes layout flash | Add shimmer skeleton placeholders while loading === true in useDashboard.js |

---

## 🟢 Priority 4 — New Features (Build After Core Is Stable)

| # | Feature | Target Files | Description |
|---|---|---|---|
| **F1** | **Backend: Real Analytics Aggregation Endpoint** | backend/api/routers/analytics.py (NEW) | GET /api/v1/analytics/summary — aggregate score trends, pillar averages, and session comparison data from all completed sessions' evaluation_report artifacts. This unblocks P2-2. |
| **F2** | **Backend: Audio Recording Download Endpoint** | backend/api/routers/voice.py | GET /api/v1/voice/recording/{session_id} — stream the saved sessions/{session_id}/recording.wav file to the browser. Required for History audio player. This unblocks P3-5. |
| **F3** | **Interview Room: Question Timer Per-Question** | frontend/src/pages/Interview.jsx | Add a per-question time indicator to the Interview Room header so candidates can self-regulate pacing. |
| **F4** | **Settings / Profile Page** | frontend/src/pages/Settings.jsx (NEW) | Candidate account settings — update display name, change password, notification preferences. Navbar "Settings" icon currently navigates nowhere. |
| **F5** | **Notifications Bell** | frontend/src/components/layout/Navbar.jsx | Navbar Bell icon is purely decorative. Wire to a dropdown of system notifications (session ready, evaluation complete) or remove the icon entirely. |
| **F6** | **Dashboard: Session Duration Metadata** | backend/api/routers/setup.py | Add duration_seconds and question_count fields to the session listing response so dashboard and history table can show interview duration without loading individual reports. |
| **F7** | **Mobile Responsive Layout Pass** | All frontend pages & CSS | Pages currently render for desktop 1280px+. Add responsive breakpoints at 768px for Setup, Dashboard, and Report pages. |
| **F8** | **Export Report as PDF** | frontend/src/pages/Report.jsx | "Download" / "Share" buttons on Report page are decorative. Wire to browser window.print() with print-specific CSS, or generate PDF via backend endpoint. |

---

## ✅ Quality Assurance & Verification Log

- ✅ **Database & Schema Verification**: Auto-migration, table creation (users, sessions, session_artifacts), and SQLite multi-thread compatibility verified.
- ✅ **Swagger UI / OpenAPI**: Verified at http://localhost:8000/docs.
- ✅ **Stage 1 & 2 Pipeline**: 22 integration tests passed, confirming background execution, 7 status checkpoints, and question preview generation.
- ✅ **Stage 3 Live Voice Engine**: End-to-end full-duplex WebSocket verified using Postman (ws://127.0.0.1:8000/api/v1/voice/stream/{session_id}?token=...).
- ✅ **Stage 4 Multimodal Reports API**: Automated test suite passed — POST 202 Accepted and GET 200 OK report retrieval verified.
- ✅ **Frontend Build (Phase 2 complete)**: npm run build — 1,693 modules, 0 errors, 0 warnings.
- ✅ **CORS Preflight Fix**: http://localhost:5173 + http://127.0.0.1:5173 verified returning Access-Control-Allow-Origin on OPTIONS.
- ✅ **Reduced Motion Support**: @media (prefers-reduced-motion: reduce) applied in animations.css — confirmed present.
- ✅ **Iconography Audit**: All emojis replaced with Lucide SVG icons across WelcomeBanner, LaunchPractice, LastSessionCard, TemplatePicker.
- ✅ **Agent Skills**: 10 frontend UI/UX skills active in .agents/skills/, Rule 12/13/14/15 in both AGENTS.md and doc/rule.md.
- ✅ **Priority 1 Bug Fixes Verified**: P1-1, P1-2, P1-3, P1-4, P1-5 completed and verified with clean `npm run build` (1,693 modules, 0 errors) and backend `scan_code_quality.py`.
- ✅ **Git Commit — Phase 2 Full Frontend**: Committed feat(frontend): add Configure Practice Track, Live Mock Interview room, Report Scorecard, History, Auth, Error Boundary, animated Eva persona (hash 55787bc).

---

## 📋 Known Technical Debt

| Item | Notes |
|---|---|
| analyticsService.js | Entirely hardcoded fiction — blocked until real analytics backend endpoint (F1) is built |
| History.jsx defaultHistoryRecords | Fake mock data fallback — must be replaced with proper empty state (P2-1) |
| PostgreSQL Migration | DATABASE_URL swap from SQLite to PostgreSQL/Supabase not yet production-validated |
| Admin Evaluation View | RBAC-protected admin endpoints for accessing all candidate sessions not yet built |
