# Netran AI — Complete Backend Architecture Plan

This document serves as the master specification for the Netran AI FastAPI backend, covering the complete folder structure, database schema, security flows, real-time WebSocket communication, and API routing.

---

## 1. Core Technology Stack

* **Framework:** FastAPI (Python 3.12+, Uvicorn, Asyncio)
* **Validation:** Pydantic v2 (Strict type checking and schema enforcement)
* **Database:** SQLite 3 (using SQLAlchemy / SQLModel with native JSON support; zero-code migration path to PostgreSQL/Supabase via `DATABASE_URL`)
* **Authentication:** OAuth2 + JWT (`python-jose` for tokens, `passlib[bcrypt]` for password hashing)
* **File Ingestion:** `pypdf`, `python-docx`
* **AI Integrations:**
  * `google-genai` SDK — Gemini `gemini-3.6-flash` (Stages 1, 2 & 4)
  * Faster-Whisper CTranslate2 `small` int8 — Offline STT (Stage 3)
  * Silero VAD v3 ONNX Runtime — Voice Activity Detection (Stage 3)
  * Kokoro-82M (PyTorch / KPipeline) — Neural TTS (Stage 3)
  * Ollama Qwen 2.5 3B — Local LLM Brain (Stage 3)
  * Ollama Qwen 2.5 1.5B — Hybrid Turn Classifier (Stage 3)

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
│   ├── stt_engine.py        # Faster-Whisper offline loader (HF_HUB_OFFLINE=1)
│   ├── tts_engine.py        # Kokoro-82M persistent stream handler
│   ├── vad_engine.py        # Silero VAD v3 ONNX + fixed 20x pre-gain + IIR DC blocker
│   └── ollama_client.py     # Local Qwen 2.5 streaming integration (3B brain + 1.5B classifier)
├── pipelines/
│   ├── jd_parser.py         # Stage 1: Gemini extraction & Tavily web research
│   └── question_tree.py     # Stage 2: 15-question stratified generation
├── data/                    # Local storage volume
│   ├── cache.db             # SQLite Database file
│   └── sessions/            # Disk storage for session recording.wav files
├── .env                     # Secrets and configurations
└── requirements.txt         # Python dependencies
```

---

## 3. Database Schema (SQLite)

We use SQLite with native `JSON` columns to handle dynamic AI outputs seamlessly. The schema uses SHA-256 input-hash deduplication to skip redundant Gemini pipeline runs.

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
| `jd_detail` | JSON | **[Stage 1]** Deep web research, company context, and role intelligence. |
| `resume_analysis` | JSON | **[Stage 2]** Skill gap matrix, candidate highlights, and red flags. |
| `interview_behavior` | JSON | **[Stage 2]** Eva persona (tone, system prompt, `whisper_domain_vocabulary`). |
| `question_tree` | JSON | **[Stage 2]** Stratified 15-question interview tree. |
| `transcript` | JSON | **[Stage 3]** Full per-turn transcript with ms-precision telemetry (`stt_ms`, `ttft_ms`, `ttfa_ms`). |
| `evaluation_report` | JSON | **[Stage 4]** Final Gemini 3-branch multimodal AI assessment. |

> **Note:** The only binary file stored to disk is `sessions/<session_id>/recording.wav` (continuous raw PCM mic audio). All other artifacts are stored as JSON columns.

---

## 4. Security & Authentication Flow (OAuth2 + JWT)

1. **REST Authentication**: Users sign up and log in via the `/api/v1/auth/` routes. Passwords are encrypted via bcrypt. A signed JWT containing the user ID and role is returned. The Next.js frontend stores this and attaches `Authorization: Bearer <token>` to all HTTP requests.
2. **WebSocket Authentication**: Because the native browser WebSocket API does not allow custom HTTP headers during the connection handshake, WebSocket authentication is handled securely via query parameters:

```javascript
// Client connection
const ws = new WebSocket(`ws://localhost:8000/api/v1/voice/stream/${sessionId}?token=${jwtToken}`);
```

FastAPI intercepts this query parameter in `dependencies.py` and validates the token before accepting the connection.

3. **Role-Based Access Control (RBAC)**: Admin accounts can fetch session logs for all users, whereas candidates can only query data matching their own `user_id`.

---

## 5. API Endpoint Specifications

### Auth (`routers/auth.py`)

* `POST /api/v1/auth/signup` — Creates a new user.
* `POST /api/v1/auth/login` — Validates credentials, returns JWT.
* `GET /api/v1/auth/me` — Validates JWT, returns current user profile.

### Document Ingestion (`routers/ingest.py`)

* `POST /api/v1/ingest/resume` — Accepts `multipart/form-data` (`.pdf`, `.docx`, `.txt`). Extracts text, standardizes to JSON via Gemini, and saves to SQLite.
* `POST /api/v1/ingest/jd` — Accepts raw pasted text. Extracts core competencies, seniority, and stack into standard JSON.

### Setup & Processing (`routers/setup.py` & `routers/questions.py`)

* `POST /api/v1/setup/analyze` — Triggers **Stage 1 & 2** AI Pipelines via FastAPI `BackgroundTasks`.
  * Runs Stage 1: Tavily web search + Gemini rubric → saves `jd_detail`.
  * Runs Stage 2: Resume analysis + question tree generation → saves `resume_analysis`, `interview_behavior`, `question_tree`.
  * Updates DB `status` to `ready` upon completion.
* `GET /api/v1/questions/preview/{session_id}` — Fetches the generated question tree for candidate review before the interview begins.

### Stage 3: Live Voice Stream (`routers/voice.py`)

* `WS /api/v1/voice/stream/{session_id}` — Bidirectional WebSocket handler.
  * Pulls `interview_behavior`, `question_tree`, and `resume_analysis` from SQLite.
  * Injects `whisper_domain_vocabulary` from `interview_behavior` as a Whisper initial prompt.
  * Instantiates and manages a `SessionState` object per connection for thread-safe signal coordination (barge-in events, agent speaking flag, pause tolerance, echo guard).

### Stage 4: Evaluation (`routers/reports.py`)

* `POST /api/v1/reports/generate/{session_id}` — Triggers Stage 4 multimodal evaluation via `BackgroundTasks`.
* `GET /api/v1/reports/{session_id}` — Fetches the finalized feedback report.

---

## 6. Voice WebSocket & DSP Audio Protocol

To ensure seamless conversational interaction with the local AI (Stage 3), the frontend and backend adhere to strict audio data protocols.

### Client → Server (Inbound PCM Stream)

1. **Audio Formatting:** The browser captures audio natively as WebM/Opus. The Next.js frontend uses an `AudioWorklet` to convert this to **16-bit, 16kHz Mono PCM bytes** before streaming it over the WebSocket.
2. **Fixed Hardware Pre-Gain:** Incoming PCM frames are scaled by a **fixed 20x pre-gain multiplier** at the top of the DSP pipeline (before any model inference) to normalize low-volume microphone hardware. This ensures Silero VAD, Whisper STT, and calibration gates all receive a properly-scaled signal without dynamic AGC destroying the temporal envelope shape.
3. **Streaming IIR DC Blocker (Pre-VAD):** A per-sample IIR high-pass filter (`alpha=0.995`, ~5Hz cutoff at 16kHz) is applied to every audio frame BEFORE Silero VAD inference. This removes microphone DC offset that saturates Silero's RNN hidden state. The filter carries state across chunks for temporal continuity — do NOT use per-chunk mean subtraction.
4. **Silero VAD Speech Gating:**
   * Speech START: `(VAD prob >= 0.30 AND rms >= 2.5× ambient_floor)` OR `VAD prob >= 0.50`
   * Speech CONTINUATION: silence counter increments only when `rms < 1.8× ambient_floor`
   * Default pause tolerance (silence timeout before endpointing): **800ms** (configurable via `SessionState.pause_tolerance_ms`).
5. **Hybrid Turn Classifier (Pre-Endpointing):** When the initial silence threshold is hit, a 2-tier turn classifier evaluates if the candidate's thought is complete before finalizing the turn:
   * **Tier 1 (Regex, 0ms):** Checks trailing conjunctions and filler words.
   * **Tier 2 (Qwen 2.5 1.5B, ~100ms):** Sends transcript to local Ollama for completion check. Extends wait up to 2300ms if incomplete.
6. **Speaker Verification:** SpeechBrain ECAPA-TDNN auto-enrolls the candidate's voice from the first utterance ≥ 2 seconds (icebreaker) and verifies cosine similarity (threshold 0.55) before every subsequent transcription.

### Server → Client (Outbound TTS Stream)

1. **Kokoro-82M Neural TTS:** Streams synthesized audio chunks to the client. TTFA (Time-To-First-Audio) is under 250ms.
2. **Barge-In / Interruption Handling:** Silero VAD runs continuously even while the agent is speaking (`state.is_agent_speaking` is set). If speech probability exceeds 0.65 during TTS playback:
   * A 300ms interrupt cooldown check prevents rapid re-triggering.
   * `state.interrupt_event` is set and `force_stop_all()` flushes the hardware audio buffer.
   * FastAPI sends an `{"event": "INTERRUPT"}` JSON frame down the WebSocket.
   * The Next.js frontend intercepts this and instantly flushes its Web Audio playback buffer.
3. **Post-TTS Echo Guard:** A 300ms monotonic timestamp guard (`_echo_guard_until`) suppresses VAD triggers after TTS completes to absorb room acoustic reflections and prevent self-capture.

### SessionState (Thread-Safe Signal Bus)

The `SessionState` dataclass is instantiated once per voice session and passed into `listen_and_transcribe()`. It coordinates signals across the DSP pipeline, barge-in watcher, and LLM/TTS threads:

| Field | Type | Purpose |
| --- | --- | --- |
| `is_agent_speaking` | `threading.Event` | Set while Kokoro TTS is playing audio. Gates echo guard and barge-in cooldown. |
| `interrupt_event` | `threading.Event` | Set by barge-in watcher to signal the LLM/TTS loop to abort. |
| `force_speech_done` | `threading.Event` | Set by `stop()` to unblock the listener loop immediately. |
| `is_candidate_speaking` | `threading.Event` | Set while candidate audio frames are actively accumulating. |
| `pause_tolerance_ms` | `int` | Silence timeout in milliseconds before endpointing (default: 800ms). |
| `tts_speed` | `float` | Dynamic Kokoro synthesis speed factor. |
| `selected_voice` | `str` | Kokoro TTS voice preset. |

---

## 7. Smart Caching System

To avoid burning unnecessary Gemini API tokens or waiting for redundant generations, the system implements **Input-Hash Deduplication**.

* When a candidate uploads a Resume and JD, FastAPI concatenates the raw texts and computes a **SHA-256 fingerprint**.
* If a session with an identical `resume_hash` + `jd_hash` already exists and successfully completed Stage 2, the backend skips the Gemini processing phase entirely and loads pre-generated artifacts directly from SQLite.
* Each stage model also maintains its own local `cache.db` (SQLite) for standalone test runs.

---

## 8. Next Steps (Phase 2 Roadmap)

1. **FastAPI Web API Gateway:** Build the `api/` layer described in Section 2, starting with `auth.py`, `ingest.py`, and `setup.py`.
2. **WebSocket Voice Handler (`voice.py`):** Wire `listen_and_transcribe()` (from `model/voice_to_voice_model/model/listener.py`) into the WebSocket endpoint using the `SessionState` signal bus.
3. **Next.js Web Frontend:** Develop the web client with `AudioWorklet` for PCM streaming, JWT auth, and real-time interview UI with barge-in support.
4. **PostgreSQL Migration:** Swap `DATABASE_URL` in `.env` to connect to a hosted PostgreSQL/Supabase instance for multi-user production deployment.
