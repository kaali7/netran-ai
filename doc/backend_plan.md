# Netran AI — Complete Backend Architecture Specification

This document serves as the master specification for the Netran AI FastAPI backend, covering the complete folder structure, database schema, security flows, real-time WebSocket communication, and API routing.

---

## 1. Core Technology Stack

* **Framework:** FastAPI (Python 3.12+, Uvicorn, Asyncio)
* **Validation:** Pydantic v2 (Strict type checking and schema enforcement)
* **Database:** SQLite 3 (using SQLAlchemy with native JSON support; zero-code migration path to PostgreSQL/Supabase via `DATABASE_URL`)
* **Authentication:** OAuth2 + JWT (`python-jose` for tokens, `passlib[bcrypt]` for password hashing)
* **File Ingestion:** `pypdf`, `python-docx`
* **AI Integrations:**
  * `google-genai` SDK — Gemini `gemini-3.6-flash` (Stages 1, 2 & 4)
  * Faster-Whisper CTranslate2 `small` int8 — Offline STT (Stage 3)
  * Silero VAD v3 ONNX Runtime — Voice Activity Detection (Stage 3)
  * Kokoro-82M (PyTorch / KPipeline) — Neural TTS (Stage 3)
  * Ollama Qwen 2.5 3B — Local LLM Brain (Stage 3)
  * Ollama Qwen 2.5 3B — Hybrid Turn Classifier (Stage 3)
  * SpeechBrain ECAPA-TDNN — Candidate Speaker Verification (Stage 3)

---

## 2. Directory & File Structure

```text
backend/
├── api/
│   ├── main.py              # FastAPI entry point, CORS middleware, app initialization
│   ├── config.py            # Environment variables loader (JWT secret, DB URL, keys)
│   ├── db.py                # SQLAlchemy engine, session maker, DB initialization
│   ├── models.py            # SQLAlchemy DB table schemas (Users, Sessions, Artifacts, Notifications)
│   ├── schemas.py           # Pydantic v2 schemas (Requests, Responses, JWT payloads, Notifications)
│   ├── security.py          # Bcrypt hashing & JWT encode/decode logic
│   ├── dependencies.py      # Dependency injection (get_db, get_current_user, get_ws_user)
│   └── routers/
│       ├── auth.py          # Authentication (/signup, /login, /me, /profile, /change-password)
│       ├── ingest.py        # Document parsing (/ingest/resume, /ingest/jd)
│       ├── setup.py         # Triggers Stage 1 & 2 (/setup/analyze, /setup/sessions)
│       ├── questions.py     # Stage 2 preview (/questions/{session_id})
│       ├── voice.py         # Stage 3 WebSockets (WS /voice/stream/{session_id})
│       ├── reports.py       # Stage 4 Multimodal evaluation (/reports/{session_id})
│       ├── template.py      # Pre-built interview templates (/template/list, /template/start)
│       ├── analytics.py     # Candidate performance telemetry (/analytics/summary)
│       ├── history.py       # Candidate archives & question details (/history/sessions, /history/detail/{id})
│       └── notifications.py # Real-time candidate alerts (/notifications)
├── data/                    # Local storage volume
│   ├── cache.db             # SQLite Database file
│   ├── sample_interviews/   # Pre-built template interview tracks (backend, frontend, fullstack)
│   └── sessions/            # Disk storage for session recording.wav and audio artifacts
├── model/                   # AI pipeline core stages (research_model, question_model, voice_to_voice_model, reports_model)
├── .env                     # Secrets and configurations
└── requirements.txt         # Python dependencies
```

---

## 3. Database Schema (SQLite)

We use SQLite with native `JSON` columns to handle dynamic AI outputs seamlessly.

### `users`

| Column | Type | Description |
| --- | --- | --- |
| `id` | String / UUID (PK) | Unique user identifier. |
| `email` | String | User login email (Indexed, Unique). |
| `display_name` | String (Nullable) | Candidate full display name. |
| `hashed_password` | String | Bcrypt hash of the password. |
| `role` | String | `candidate` or `admin`. |
| `created_at` | DateTime | Account creation timestamp. |

### `sessions`

| Column | Type | Description |
| --- | --- | --- |
| `id` | String / UUID (PK) | Unique interview session identifier. |
| `user_id` | String / UUID (FK) | Foreign key linked to `users.id`. |
| `resume_hash` | String | SHA-256 hash of candidate resume. |
| `jd_hash` | String | SHA-256 hash of Job Description. |
| `status` | Enum | `setup`, `analyzing`, `ready`, `in_progress`, `evaluating`, `completed`. |
| `progress_message` | String | Progress message during background pipeline runs. |
| `created_at` | DateTime | Session initialization timestamp. |

### `session_artifacts`

| Column | Type | Description |
| --- | --- | --- |
| `id` | Integer (PK) | Auto-incrementing primary key. |
| `session_id` | String / UUID (FK) | Foreign key linked to `sessions.id`. |
| `parsed_resume` | JSON | Standardized schema of candidate skills/experience. |
| `parsed_jd` | JSON | Standardized schema of job requirements. |
| `jd_detail` | JSON | **[Stage 1]** Deep web research, company context, and role intelligence. |
| `resume_analysis` | JSON | **[Stage 2]** Skill gap matrix, candidate highlights, and red flags. |
| `interview_behavior` | JSON | **[Stage 2]** Eva persona (system prompt, `whisper_domain_vocabulary`). |
| `question_tree` | JSON | **[Stage 2]** Stratified 15-question interview tree. |
| `transcript` | JSON | **[Stage 3]** Full per-turn transcript with ms-precision telemetry. |
| `evaluation_report` | JSON | **[Stage 4]** Final Gemini 3-branch multimodal AI assessment. |

### `notifications`

| Column | Type | Description |
| --- | --- | --- |
| `id` | String / UUID (PK) | Unique notification identifier. |
| `user_id` | String / UUID (FK) | Foreign key linked to `users.id`. |
| `title` | String | Notification header text. |
| `message` | Text | Detailed notification message. |
| `type` | String | Category (`report`, `setup`, `welcome`, `system`). |
| `link` | String (Nullable) | Direct navigation path (e.g. `/report/{id}`, `/history`). |
| `read` | Boolean | Read state indicator (default: `False`). |
| `created_at` | DateTime | Timestamp of creation. |

---

## 4. Security & Authentication Flow (OAuth2 + JWT)

1. **REST Authentication**: Users sign up and log in via `/api/v1/auth/`. Passwords are encrypted via bcrypt. A signed JWT containing user ID is returned and attached via `Authorization: Bearer <token>` header.
2. **WebSocket Authentication**: Handled via query parameter:
   ```javascript
   const ws = new WebSocket(`ws://localhost:8000/api/v1/voice/stream/${sessionId}?token=${jwtToken}`);
   ```
   FastAPI validates the token in `dependencies.py` before accepting the connection.
3. **Profile & Security Endpoints**: Candidates can update their `display_name` via `PATCH /api/v1/auth/profile` and change credentials securely via `POST /api/v1/auth/change-password`.

---

## 5. API Endpoint Specifications

### Auth (`routers/auth.py`)
* `POST /api/v1/auth/signup` — Registers a new candidate.
* `POST /api/v1/auth/login` — Authenticates credentials, returns JWT.
* `GET /api/v1/auth/me` — Fetches authenticated user profile.
* `PATCH /api/v1/auth/profile` — Updates candidate `display_name`.
* `POST /api/v1/auth/change-password` — Updates password with current password verification.

### Notifications (`routers/notifications.py`)
* `GET /api/v1/notifications` — Lists candidate alerts with unread counter (auto-seeds welcome message).
* `PATCH /api/v1/notifications/{id}/read` — Marks single notification as read.
* `POST /api/v1/notifications/mark-all-read` — Marks all notifications as read.
* `DELETE /api/v1/notifications/{id}` — Deletes single notification.

### Document Ingestion (`routers/ingest.py`)
* `POST /api/v1/ingest/resume` — Accepts `.pdf`, `.docx`, `.txt`. Extracts text, parses to JSON schema via Gemini.
* `POST /api/v1/ingest/jd` — Ingests raw job description text.

### Setup & Questions (`routers/setup.py` & `routers/questions.py`)
* `POST /api/v1/setup/analyze` — Triggers Stage 1 & 2 background pipeline runner.
* `GET /api/v1/setup/sessions` — Lists user interview sessions.
* `GET /api/v1/questions/preview/{session_id}` — Fetches generated question tree.

### Template Mock Interviews (`routers/template.py`)
* `GET /api/v1/template/list` — Returns pre-built template catalog (Backend, Frontend, Full Stack AI).
* `POST /api/v1/template/start` — Instantly creates and seeds a personalized mock interview session.

### Stage 3: Live Voice Stream (`routers/voice.py`)
* `WS /api/v1/voice/stream/{session_id}` — Bidirectional full-duplex WebSocket handler.
  * Streams raw 16kHz PCM audio frames.
  * Implements Silero VAD, Faster-Whisper STT, Kokoro TTS, and barge-in interruption.

### Stage 4: Evaluation & Telemetry (`routers/reports.py`, `analytics.py`, `history.py`)
* `POST /api/v1/reports/generate/{session_id}` — Triggers Stage 4 multimodal evaluation.
* `GET /api/v1/reports/{session_id}` — Fetches completed evaluation scorecard.
* `GET /api/v1/analytics/summary` — Aggregates readiness, scores, and skills radar data.
* `GET /api/v1/history/sessions` — Returns paginated history archive with search & filter.
