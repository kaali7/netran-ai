# Netran AI — Complete Backend Architecture Plan

This document serves as the master specification for the Netran AI FastAPI backend, covering the complete folder structure, database schema, security flows, real-time WebSocket communication, and API routing.

## 1. Core Technology Stack

* **Framework:** FastAPI (Python 3.12+, Uvicorn, Asyncio)
* **Validation:** Pydantic v2 (Strict type checking and schema enforcement)
* **Database:** SQLite 3 (using SQLAlchemy / SQLModel with native JSON support)
* **Authentication:** OAuth2 + JWT (`python-jose` for tokens, `passlib[bcrypt]` for password hashing)
* **File Ingestion:** `pypdf`, `python-docx`
* **AI Integrations:** `google-genai` (Gemini 3.6-flash), Faster-Whisper (STT), Silero VAD (Voice Activity Detection), Kokoro-82M (TTS), Ollama (Local Qwen 2.5)

---

## 2. Directory & File Structure

The `backend/` directory is designed for modularity, separating routing logic from database models and background processing.

```text
backend/
├── api/
│   ├── main.py              # FastAPI entry point, CORS middleware, app initialization
│   ├── config.py            # Environment variables loader (JWT secret, DB URL, keys)
│   ├── db.py                # SQLAlchemy engine, session maker, DB initialization
│   ├── models.py            # SQLAlchemy DB table schemas (Users, Sessions, Artifacts)
│   ├── schemas.py           # Pydantic v2 schemas (Requests, Responses, JWT payloads)
│   ├── security.py          # Bcrypt hashing & JWT encode/decode logic
│   ├── dependencies.py      # Dependency injection (get_db, get_current_user)
│   └── routers/
│       ├── auth.py          # Authentication (/signup, /login, /me)
│       ├── ingest.py        # Document parsing (/ingest/resume, /ingest/jd)
│       ├── setup.py         # Triggers Stage 1 & 2 (/setup/analyze)
│       ├── questions.py     # Stage 2 preview (/questions/{session_id})
│       ├── voice.py         # Stage 3 WebSockets (WS /voice/stream/{session_id})
│       └── reports.py       # Stage 4 Multimodal evaluation (/reports/{session_id})
├── core/
│   ├── stt_engine.py        # Faster-Whisper offline loader
│   ├── tts_engine.py        # Kokoro-82M persistent stream handler
│   ├── vad_engine.py        # Silero VAD & audio chunk filtering
│   └── ollama_client.py     # Local Qwen 2.5 streaming integration
├── pipelines/
│   ├── jd_parser.py         # Stage 1: Gemini extraction & web research
│   └── question_tree.py     # Stage 2: 15-question stratified generation
├── data/                    # Local storage volume
│   ├── cache.db             # SQLite Database file
│   └── sessions/            # Disk storage for session recording.wav files
├── .env                     # Secrets and configurations
└── requirements.txt         # Python dependencies

```

---

## 3. Database Schema (SQLite)

We will use SQLite with native `JSON` columns to handle dynamic AI outputs seamlessly without writing messy `.json` files to the disk.

### `users`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID (PK) | Unique user identifier. |
| `email` | String | User login email (Indexed, Unique). |
| `hashed_password` | String | Bcrypt hash of the password. |
| `role` | Enum | `candidate` or `admin`. |
| `created_at` | DateTime | Account creation timestamp. |

### `sessions`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID (PK) | Unique interview session identifier. |
| `user_id` | UUID (FK) | Foreign key linked to `users.id`. |
| `resume_hash` | String | SHA-256 hash of candidate resume (used for caching). |
| `jd_hash` | String | SHA-256 hash of Job Description. |
| `status` | Enum | `setup`, `analyzing`, `ready`, `in_progress`, `evaluating`, `completed`. |
| `created_at` | DateTime | Session initialization timestamp. |

### `session_artifacts` *(Core Knowledge & Context)*

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID (PK) | Unique artifact identifier. |
| `session_id` | UUID (FK) | Foreign key linked to `sessions.id`. |
| `parsed_resume` | JSON | Standardized schema of candidate skills/experience. |
| `parsed_jd` | JSON | Standardized schema of job requirements. |
| `jd_detail` | JSON | **[Stage 1]** Deep web research, company context, and role intelligence extracted during the setup phase. |
| `interview_behavior` | JSON | **[Config]** Eva's persona settings (tone, strictness, system prompt logic) used dynamically in Stage 2 and Stage 3. |
| `question_tree` | JSON | **[Stage 2]** Stratified interview questions generated based on `jd_detail` and `interview_behavior`. |
| `transcript` | JSON | **[Stage 3]** Full conversational transcript array (User/Eva). |
| `evaluation_report` | JSON | **[Stage 4]** Final AI assessment. |

---

## 4. Security & Authentication Flow (OAuth2 + JWT)

1. **REST Authentication**: Users sign up and log in via the `/api/v1/auth/` routes. Passwords are encrypted via bcrypt. A signed JWT containing the user ID and role is returned. The Next.js frontend stores this and attaches `Authorization: Bearer <token>` to all HTTP requests.
2. **WebSocket Authentication**: Because the native browser WebSocket API does not allow for custom HTTP headers during the connection handshake, WebSocket authentication is handled securely via query parameters:
```javascript
// Client connection
const ws = new WebSocket(`ws://localhost:8000/api/v1/voice/stream/${sessionId}?token=${jwtToken}`);

```


FastAPI intercepts this query parameter in `dependencies.py` and validates the token before accepting the connection.
3. **Role-Based Access Control (RBAC)**: Admin accounts can fetch session logs for all users, whereas candidates can only query data matching their own `user_id`.

---

## 5. API Endpoint Specifications

### Auth (`routers/auth.py`)

* `POST /api/v1/auth/signup` - Creates a new user.
* `POST /api/v1/auth/login` - Validates credentials, returns JWT.
* `GET /api/v1/auth/me` - Validates JWT, returns current user profile.

### Document Ingestion (`routers/ingest.py`)

* `POST /api/v1/ingest/resume` - Accepts `multipart/form-data` (`.pdf`, `.docx`, `.txt`). Extracts text, standardizes to JSON using Gemini, and saves to SQLite.
* `POST /api/v1/ingest/jd` - Accepts raw pasted text. Extracts core competencies, seniority, and stack into standard JSON.

### Setup & Processing (`routers/setup.py` & `routers/questions.py`)

* `POST /api/v1/setup/analyze` - Triggers **Stage 1 & 2** AI Pipelines via FastAPI `BackgroundTasks`.
* *Generates `jd_detail` by researching the company/role.*
* *Generates `interview_behavior` rules tailored to the role's seniority.*
* Updates DB status to `ready` upon completion.


* `GET /api/v1/questions/preview/{session_id}` - Fetches the generated question tree for candidate review before the interview begins.

### Stage 3: Live Voice Stream (`routers/voice.py`)

* `WS /api/v1/voice/stream/{session_id}` - Bidirectional WebSocket handler. Pulls `interview_behavior` and `jd_detail` from SQLite to contextually prompt the local LLM.

### Stage 4: Evaluation (`routers/reports.py`)

* `POST /api/v1/reports/generate/{session_id}` - Triggers Stage 4 multimodal evaluation via `BackgroundTasks`.
* `GET /api/v1/reports/{session_id}` - Fetches the finalized feedback report.

---

## 6. Voice WebSocket & DSP Protocol

To ensure seamless conversational interaction with the local AI (Stage 3), the frontend and backend adhere to strict audio data protocols.

1. **Audio Formatting:** The browser captures audio natively as WebM/Opus. The Next.js frontend uses an `AudioWorklet` to convert this to **16-bit, 16kHz Mono PCM bytes** before streaming it over the WebSocket.
2. **DSP Filtering:** FastAPI runs the incoming bytes through a High-Pass IIR Filter (`alpha=0.995`) to remove DC offset/drift, ensuring pristine audio reaches Silero VAD and Faster-Whisper.
3. **Barge-In / Interruption Handling:** If the AI is currently talking (via Kokoro TTS) and Silero VAD detects new candidate speech, FastAPI immediately sends an `{"event": "INTERRUPT"}` JSON frame down the WebSocket. The Next.js frontend intercepts this and instantly flushes its Web Audio playback buffer to stop the AI's voice.

---

## 7. Smart Caching System

To avoid burning unnecessary Gemini API tokens or waiting for redundant generations, the system implements **Input-Hash Deduplication**.

* When a candidate uploads a Resume and JD, FastAPI concatenates the raw texts and computes a **SHA-256 fingerprint**.
* If a session with an identical `resume_hash` + `jd_hash` already exists and successfully completed Stage 2, the backend skips the Gemini processing phase entirelyHere is how you can update your database schema to add these two missing columns to `session_artifacts`.

---

## SQL Migration Script

If you are executing a raw SQL query (e.g., PostgreSQL, MySQL, SQLite), you can add these columns using an `ALTER TABLE` statement:

```sql
ALTER TABLE session_artifacts
ADD COLUMN jd_detail TEXT,
ADD COLUMN interview_behaviour TEXT;

```

> **Note on naming:** Fixed the spelling from `intreview` to `interview`.

---

## Data Type Recommendations

Depending on how your question generation model and voice pipeline consume this data, you might want to consider `JSONB` / `JSON` instead of plain text:

| Column Name | Recommended Type | Usage / Format |
| --- | --- | --- |
| **`jd_detail`** | `TEXT` or `JSONB` | **`TEXT`**: If storing raw scraped text or Markdown summaries.<br>

<br>**`JSONB`**: If storing parsed structure (e.g., `{"company_culture": "...", "tech_stack": [...], "key_responsibilities": [...]}`). |
| **`interview_behaviour`** | `TEXT` or `JSONB` | **`TEXT`**: System prompt directives for Eva (e.g., *"Eva should act as a senior system architect, remaining encouraging but strict on deep technical accuracy"*).<br>

<br>**`JSONB`**: Structured settings (e.g., `{"tone": "friendly", "pacing": "fast", "strictness_level": 4}`). |

---

## Prisma Schema Example (If using Prisma)

If you are using an ORM like Prisma, update your `schema.prisma` file like this:

```prisma
model SessionArtifacts {
  id                  String   @id @default(uuid())
  // ... other existing fields
  jd_detail           String?  @db.Text // or Json?
  interview_behaviour String?  @db.Text // or Json?
}

```

Then run your migration command:

```bash
npx prisma migrate dev --name add_jd_and_behaviour_to_session_artifacts

```
