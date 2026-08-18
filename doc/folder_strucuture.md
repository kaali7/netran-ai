# Netran AI Backend — Folder Structure & File Inventory

This document details the complete, clean directory structure and file inventory of the Netran AI backend model architecture.

---

## 🏗️ Master Tree Overview

```text
.agents/                       # AI Agent custom instructions and tool skills (Root Level)
├── AGENTS.md                  # AI Agent Workspace Rules
└── skills/                    # AI capability extensions (gemini-interactions-api, ui-ux-pro-max, animate, etc.)
skills-lock.json               # Locked agent skill registry (Root Level)
DESIGN.md                      # Design System Tokens & Serene Learning Guidelines
run.bat                        # Master Interactive Batch Launcher (Backend & Frontend)
.gitignore                     # Master Git Ignore Rules (Root Level)

doc/                           # Master System Documentation (Root Level)
├── backend_plan.md            # Backend milestone implementation plan
├── current.md                 # Current system status & architecture overview
├── folder_strucuture.md       # Complete folder structure & file inventory
├── frontend_structure.md      # Frontend architecture, components & design tokens
├── rule.md                    # Mandatory system rules & developer directives
├── task_completion.md         # Task completion tracker & deliverables matrix
└── tech_stack.md              # Technical stack specifications

frontend/                      # React 18 + Vite 5 Web Client
├── public/                    # Static brand assets (favicon.svg)
├── src/
│   ├── assets/                # Icons & UI artwork
│   ├── components/
│   │   ├── layout/            # Navbar.jsx (Profile Sub-Menu), PageWrapper.jsx
│   │   ├── ui/                # Card.jsx, Button.jsx, Badge.jsx, StatCard.jsx, ProgressBar.jsx
│   │   ├── dashboard/         # WelcomeBanner.jsx, StatsRow.jsx, LaunchPractice.jsx, LastSessionCard.jsx, SessionsTable.jsx, TemplatePicker.jsx
│   │   └── interview/         # AvatarEva.jsx
│   ├── hooks/                 # useDashboard.js, useAuth.js, useInterviewSession.js, useSetup.js, useReports.js
│   ├── pages/                 # Dashboard.jsx, Setup.jsx, Analytics.jsx, History.jsx, Interview.jsx, Processing.jsx, Report.jsx, Login.jsx
│   ├── services/              # api.js, authService.js, sessionService.js, templateService.js, reportService.js, analyticsService.js
│   ├── store/                 # authStore.js (Zustand JWT auth store)
│   ├── styles/                # index.css (tokens & custom scrollbar), glass.css (glassmorphism), animations.css
│   ├── utils/                 # constants.js
│   ├── App.jsx                # App shell
│   ├── main.jsx               # Bootstrap root
│   └── router.jsx             # React Router v6 with ProtectedRoute / PublicRoute guards & v7 future flags
├── index.html                 # Manrope font import & HTML shell
├── package.json               # React 18, Vite 5, Lucide-React, Axios, Zustand
└── vite.config.js             # Vite config with backend reverse proxy (/api -> :8000)

backend/
├── .env                       # Root environment secrets (GEMINI_API_KEY, TAVILY_API_KEY, OLLAMA_MODEL)
├── .gitignore                 # Backend git ignore rules
├── check_dependencies.py      # Environment, Ollama, HuggingFace model & API key checker
├── README.md                  # System overview & developer instructions
├── requirements.txt           # Master unified Python dependencies list
├── scan_code_quality.py       # Automated code quality and docstring scanner script

├── api/                       # FastAPI Web API Gateway
│   ├── __init__.py            # API package initializer
│   ├── main.py                # FastAPI entry point, CORS middleware, app initialization
│   ├── config.py              # Environment variables loader (JWT secret, DB URL, keys)
│   ├── db.py                  # SQLAlchemy engine, session maker, DB initialization
│   ├── models.py              # SQLAlchemy DB table schemas (Users, Sessions, Artifacts)
│   ├── schemas.py             # Pydantic v2 schemas (Auth, Sessions, Health)
│   ├── security.py            # Bcrypt hashing & JWT encode/decode logic
│   ├── dependencies.py        # Dependency injection (get_db, get_current_user, get_ws_user)
│   └── routers/
│       ├── __init__.py        # Routers package initializer
│       ├── auth.py            # Authentication (/signup, /login, /me)
│       ├── ingest.py          # Document parsing stub (/ingest/resume, /ingest/jd)
│       ├── setup.py           # Stage 1 & 2 analysis trigger & candidate sessions listing (/setup/analyze, /setup/sessions)
│       ├── questions.py       # Stage 2 question preview stub (/questions/{session_id})
│       ├── voice.py           # Stage 3 WebSockets stub (WS /voice/stream/{session_id})
│       ├── reports.py         # Stage 4 evaluation stub (/reports/{session_id})
│       └── template.py        # Template Mock Interview endpoints (/template/list, /template/start)
├── data/                      # Local SQLite database, session storage & sample templates
│   └── sample_interviews/    # Pre-built interview templates (backend/, frontend/, fullstack/)
├── sessions/                  # Global active interview session artifacts ( sess_<timestamp>/ )

└── model/                     # Multi-stage AI pipeline core modules
    ├── research_model/        # STAGE 1: JD Research & Market Intelligence Engine
    │   ├── doc/
    │   │   ├── current.md     # Stage 1 technical implementation status
    │   │   └── prd.md         # Stage 1 Product Requirements Document
    │   ├── test/              # Stage 1 test harness input/output directories
    │   │   ├── input/         # Pre-saved dummy JD sample JSON files (*.json)
    │   │   └── output/        # Generated session outputs ( sess_<timestamp>.json )
    │   └── model/
    │       ├── __init__.py    # Package initializer
    │       ├── front.py       # Kivy Desktop GUI test client with web intel visualizer
    │       ├── cache.py       # SQLite hash-based caching engine (cache.db)
    │       ├── config.py      # Stage 1 configuration & environment loader (TRUSTED_DOMAINS)
    │       ├── gemini_client.py # Gemini 3.6 Flash Interactions API client & REST fallback
    │       ├── jd_parser.py   # Job Description parser & search query generator
    │       ├── pipeline.py    # Stage 1 end-to-end orchestrator & artifact saver
    │       ├── prompts.py     # Centralized Stage 1 system prompt templates (JD_PARSER_PROMPT_TEMPLATE, RUBRIC_GENERATOR_PROMPT_TEMPLATE)
    │       ├── rubric_generator.py # Gemini-powered assessment rubric synthesizer
    │       ├── schemas.py     # Pydantic schemas (ParsedJD, InterviewTopic, InterviewRubric, Stage1Output)
    │       ├── search_engine.py # Tavily Search API client with expanded domain whitelist
    │       └── test_pipeline.py # Standalone Headless CLI test harness for Stage 1
    │
    ├── question_model/        # STAGE 2: Adaptive Contextual & Behavioral Intelligence Engine
    │   ├── doc/
    │   │   ├── current.md     # Stage 2 technical implementation status
    │   │   └── prd.md         # Stage 2 Product Requirements Document
    │   ├── test/              # Stage 2 test harness input/output directories
    │   │   ├── input/         # Pre-saved dummy input subdirectories (sample_backend/, sample_frontend/, sample_fullstack/)
    │   │   └── output/        # Generated session folders ( sess_<timestamp>/ -> resume_analysis.json, interview_questions.json, interviewer_behavior.json )
    │   └── model/
    │       ├── front.py       # Stage 2 Kivy Desktop GUI Client with Candidate Profile, Role Fit Scores, Question Cards, Rubrics & Session History
    │       ├── cache.py       # SQLite hash-based caching engine (cache.db) with pre-root model migration recovery
    │       ├── config.py      # Stage 2 configuration loader (Stage2Config)
    │       ├── pipeline.py    # Stage 2 master orchestrator pipeline running dual parallel Planner & Analyst calls generating 3 session artifacts
    │       ├── prompt_builder.py # Stage2PromptBuilder with Stage 1 nested JSON extractor
    │       ├── prompts.py     # Centralized Stage 2 system prompt templates (PLANNER_PROMPT_TEMPLATE, ANALYST_PROMPT_TEMPLATE)
    │       ├── question_generator.py # Backward compatibility alias for pipeline.py
    │       ├── resume_parser.py # PDF, DOCX, TXT, and JSON resume extractor
    │       ├── schemas.py     # Pydantic v2 schemas (CandidateProfile, RoleFitScoring, ExtractedSkillMatch, WorkHistoryEntry, DetailedProjectAnalysis, ExperienceGapsAndRedFlags, PlannerOutput, ResumeAnalysis, QuestionItem, InterviewerBehavior [+whisper_domain_vocabulary], Stage2Output)
    │       └── test_pipeline.py # Standalone Headless CLI test harness for Stage 2
    │
    ├── voice_to_voice_model/  # STAGE 3: Live Voice-to-Voice Streaming Loop
    │   ├── doc/
    │   │   ├── current.md     # Stage 3 technical implementation status
    │   │   └── prd.md         # Stage 3 Product Requirements Document
    │   ├── test/              # Stage 3 test harness input/output directories
    │   │   ├── input/         # Stage 2 preset inputs (interview_questions.json, interviewer_behavior.json, resume_analysis.json)
    │   │   └── output/        # Generated session folders ( sess_<timestamp>/ -> recording.wav & transcript.json )
    │   └── model/
    │       ├── benchmark.py   # Latency telemetry recorder (stt_ms, ttft_ms, ttfa_ms)
    │       ├── brain.py       # Local Ollama Qwen2.5:3b streaming LLM engine with TextSanitizer regex
    │       ├── config.py      # Stage 3 configuration loader (Stage3Config)
    │       ├── download_vad.py # Downloader utility for Silero VAD ONNX model weights
    │       ├── front.py       # Kivy Desktop GUI client for standalone Stage 3 testing
    │       ├── listener.py    # Silero VAD v3, auto-gain peak normalizer, Faster-Whisper STT
    │       ├── pipeline.py    # Stage 3 master pipeline entry point (WorkflowVoiceEngine)
    │       ├── prompts.py     # Centralized Stage 3 system prompts (SYSTEM_PROMPT, dynamic get_system_prompt() builder; WHISPER_INITIAL_PROMPT removed — now generated dynamically from Stage 2 whisper_domain_vocabulary)
    │       ├── question_manager.py # State machine & keyword density adaptive branching engine
    │       ├── schemas.py     # Pydantic v2 schemas (InterviewQuestionInput, InterviewerBehaviorInput [+whisper_domain_vocabulary], Stage2SessionBundle, TurnManifest, SessionManifest)
    │       ├── session_logger.py # Monotonic timer & transcript.json logger
    │       ├── session_state.py  # Thread-safe cross-module state/event tracker (Echo Gate)
    │       ├── silero_vad.onnx # Silero VAD neural network model weights (2.3 MB)
    │       ├── speaker.py     # Kokoro-82M neural TTS streaming playback engine
    │       ├── speaker_verifier.py # SpeechBrain ECAPA-TDNN candidate speaker verification & auto-enrollment engine
    │       ├── test_pipeline.py # Standalone Headless CLI test harness for Stage 3

    │       ├── turn_classifier.py # Case 3 Hybrid Turn Classifier (Tier 1 Regex + Tier 2 Ollama OLLAMA_MODEL, qwen2.5:3b by default)
    │       ├── voice_engine.py # Stage 3 adapter with dynamic system prompt injection (WorkflowVoiceEngine)
    │       └── _interview_log.txt # Consolidated session logging file
    │
    ├── reports_model/         # STAGE 4: Post-Session Multimodal Evaluation Engine
    │   ├── doc/
    │   │   ├── current.md     # Stage 4 technical implementation status
    │   │   └── prd.md         # Stage 4 Product Requirements Document
    │   ├── test/              # Stage 4 test harness input/output directories
    │   │   ├── input/         # Stage 3 preset input sessions (sample_session/ -> continuous_mic_input.wav & transcript.json)
    │   │   └── output/        # Generated report sessions ( sess_<timestamp>/ -> report.json & evaluation_summary.md )
    │   └── model/
    │       ├── audio_slicer.py # Non-destructive WAV slicing utility (turn_XX.wav)
    │       ├── config.py      # Stage 4 configuration loader (Stage4Config)
    │       ├── front.py       # Kivy Desktop GUI test client for Stage 4
    │       ├── gemini_evaluator.py # 3-branch Gemini multimodal evaluation engine
    │       ├── pipeline.py    # Stage 4 master orchestrator pipeline (Stage4Pipeline)
    │       ├── prompts.py     # Centralized Stage 4 system prompts (AUDIO_SYSTEM_PROMPT, TECHNICAL_SYSTEM_PROMPT, COMBINE_SYSTEM_PROMPT)
    │       ├── report_builder.py # Backward compatibility alias for pipeline.py
    │       ├── report_schema.py # Backward compatibility alias for schemas.py
    │       ├── schemas.py     # Pydantic schemas (CandidateReportPayload, TurnAnalysis, TurnTelemetry, BehavioralFlag, CandidateFeedback, PillarScore)
    │       └── test_pipeline.py # Standalone CLI test harness for Stage 4
    │
    └── workflow/              # UNIFIED WORKFLOW ORCHESTRATOR (Stage 1→4)
        ├── doc/
        │   ├── current.md     # Unified workflow technical documentation
        │   └── overall_model_process.md # High-level multi-stage architecture specification
        ├── test/              # Workflow test harness input/process/output directories
        │   ├── input/         # Preset input data (sample_session/ -> sample_job_detail.json & sample_resume.json)
        │   ├── process/       # Middle processing & cache data (sess_<timestamp>/ -> Stage 1, 2, 3 intermediate artifacts & cache.db)
        │   └── output/        # Final workflow evaluation reports (sess_<timestamp>/ -> report.json & evaluation_summary.md)
        └── model/
            ├── config.py      # Master configuration & non-colliding sys.path injector
            ├── front.py       # Unified 6-Screen Kivy Desktop Application
            ├── orchestrator.py # Master 4-stage pipeline execution coordinator
            ├── run.bat        # Duplicate workflow launcher script
            ├── sample_data.py # Demo testing data provider (loads test/input/sample_session JSON files)
            └── test_pipeline.py # Standalone Headless CLI test harness for Unified Workflow
```

---

## 📄 Key Directory Descriptions

### 1. `backend/` (Root Directory)
- **`.env`**: Stores sensitive API credentials (`GEMINI_API_KEY`, `TAVILY_API_KEY`, `OLLAMA_MODEL`).
- **`check_dependencies.py`**: Automated environment, Ollama model, Hugging Face local cache, and API key verification script.
- **`requirements.txt`**: Consolidated dependencies file for the entire backend model suite.
- **`run.bat`**: Interactive Windows Command Prompt launcher providing a 20-choice menu to run individual stage tests, maintenance routines, or the full workflow app.
- **`scan_code_quality.py`**: Automated audit script ensuring docstring coverage, single requirements.txt usage, and clean directory hygiene.

### 2. `backend/api/` (Web API Gateway)
- **`main.py`**: FastAPI entry point with CORS middleware, latency tracking telemetry, OpenAPI `/docs`, and router mounting.
- **`config.py`**: Environment variables loader parsing `.env` keys.
- **`db.py`**: SQLAlchemy engine, session maker, and DB initialization.
- **`models.py`**: ORM definitions for `User`, `Session`, and `SessionArtifact`.
- **`schemas.py`**: Pydantic v2 validation schemas.
- **`security.py`**: Bcrypt hashing and JWT encoding/decoding.
- **`dependencies.py`**: Auth and RBAC dependency injection helpers (`get_current_user`, `get_ws_user`, `require_admin`).
- **`routers/`**: Routers for `auth.py` (working), `ingest.py` (stub), `setup.py` (stub), `questions.py` (stub), `voice.py` (stub), `reports.py` (stub).

### 3. `backend/data/` (Storage Volume)
- Local SQLite database (`cache.db`) and binary audio session directories.

### 4. `doc/` (Master Documentation Volume)
- Contains system-level documentation covering the complete system architecture (`current.md`), folder structure (`folder_strucuture.md`), frontend architecture (`frontend_structure.md`), mandatory directives (`rule.md`), task tracking (`task_completion.md`), and technical stack (`tech_stack.md`).


### 5. `backend/model/`

- Contains all AI model subsystems organized cleanly into `research_model`, `question_model`, `voice_to_voice_model`, `reports_model`, and `workflow`.
- Includes `workflow/doc/overall_model_process.md` detailing the complete high-level process matrix.
- Middle process data is saved in `workflow/test/process/sess_<timestamp>/` and final report evaluation artifacts are saved in `workflow/test/output/sess_<timestamp>/`.
