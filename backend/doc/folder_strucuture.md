# Netran AI Backend — Folder Structure & File Inventory

This document details the complete, clean directory structure and file inventory of the Netran AI backend model architecture.

---

## 🏗️ Master Tree Overview

```
backend/
├── .env                       # Root environment secrets (GEMINI_API_KEY, TAVILY_API_KEY, OLLAMA_MODEL)
├── .gitignore                 # Git ignore rules (virtual environment, cache DB, WAV audio, test_output)
├── README.md                  # System overview & developer instructions
├── requirements.txt           # Master unified Python dependencies list
├── run.bat                    # Interactive Windows batch launcher (12-option menu)
├── scan_code_quality.py       # Automated code quality and docstring scanner script
├── doc/                       # System-wide backend documentation
│   ├── current.md             # Current operational state & component synthesis
│   └── folder_strucuture.md   # Detailed directory structure (this file)
├── sessions/                  # Global active interview session artifacts ( sess_<timestamp>/ )
└── model/                     # Multi-stage AI pipeline core modules
    ├── overall_model_process.md # High-level pipeline process matrix (Stage 1→4)
    ├── research_model/        # STAGE 1: JD Research & Market Intelligence Engine
    │   ├── doc/
    │   │   ├── current.md     # Stage 1 technical implementation status
    │   │   └── prd.md         # Stage 1 Product Requirements Document
    │   └── model/
    │       ├── __init__.py    # Package initializer
    │       ├── app.py         # Kivy Desktop GUI test client for Stage 1
    │       ├── cache.py       # SQLite hash-based caching engine (cache.db)
    │       ├── config.py      # Stage 1 configuration & environment loader
    │       ├── gemini_client.py # Gemini 3.6 Flash Interactions API client & REST fallback
    │       ├── jd_parser.py   # Job Description parser & search query generator
    │       ├── pipeline.py    # Stage 1 end-to-end orchestrator
    │       ├── rubric_generator.py # Gemini-powered assessment rubric synthesizer
    │       ├── schemas.py     # Pydantic schemas (ParsedJD, InterviewTopic, InterviewRubric)
    │       └── search_engine.py # Tavily Search API client with engineering domain whitelisting
    │
    ├── question_model/        # STAGE 2: Contextual Question & Behavioral Prompt Engine
    │   ├── doc/
    │   │   ├── current.md     # Stage 2 technical implementation status
    │   │   └── prd.md         # Stage 2 Product Requirements Document
    │   └── model/
    │       ├── config.py      # Stage 2 configuration loader
    │       ├── dummy_resume.txt # Standalone test resume file
    │       ├── prompt_builder.py # Stage 3 latency-constrained system prompt instruction builder
    │       ├── question_generator.py # Gemini 15-question tree & system prompt generator
    │       ├── resume_parser.py # PDF (pypdf), DOCX (python-docx), and TXT resume extractor
    │       ├── schemas.py     # Pydantic schemas (QuestionItem, Stage2Output)
    │       └── test_pipeline.py # Standalone CLI test harness for Stage 2
    │
    ├── voice_to_voice_model/  # STAGE 3: Live Voice-to-Voice Streaming Loop
    │   ├── doc/
    │   │   ├── current.md     # Stage 3 technical implementation status
    │   │   └── prd.md         # Stage 3 Product Requirements Document
    │   └── model/
    │       ├── benchmark.py   # Latency telemetry recorder (stt_ms, ttft_ms, ttfa_ms)
    │       ├── brain.py       # Local Ollama Qwen2.5:1.5b streaming LLM engine ('Eva' persona)
    │       ├── download_vad.py # Downloader utility for Silero VAD ONNX model weights
    │       ├── interview_scripts.json # Pre-scripted calibration tracks for Script Mode
    │       ├── listener.py    # Silero VAD v3, auto-gain peak normalizer, Faster-Whisper STT
    │       ├── main_app.py    # Kivy Desktop GUI client for standalone Stage 3 testing
    │       ├── session_logger.py # Monotonic timer & session_manifest.json logger
    │       ├── silero_vad.onnx # Silero VAD neural network model weights (2.3 MB)
    │       └── speaker.py     # Kokoro-82M neural TTS streaming playback engine
    │
    ├── reports_model/         # STAGE 4: Post-Session Multimodal Evaluation Engine
    │   ├── doc/
    │   │   ├── current.md     # Stage 4 technical implementation status
    │   │   └── prd.md         # Stage 4 Product Requirements Document
    │   └── model/
    │       ├── audio_slicer.py # Non-destructive WAV slicing utility (turn_XX.wav)
    │       ├── gemini_evaluator.py # 3-branch Gemini multimodal evaluation engine
    │       ├── report_builder.py # Stage 4 orchestrator & dual artifact renderer (JSON + MD)
    │       ├── report_schema.py # Pydantic schemas (CandidateReportPayload, TurnAnalysis, PillarScore)
    │       ├── test_pipeline.py # Standalone CLI test harness for Stage 4
    │       └── test_ui.py     # Kivy Desktop GUI test client for Stage 4
    │
    └── workflow/              # UNIFIED WORKFLOW ORCHESTRATOR (Stage 1→4)
        ├── doc/
        │   └── current.md     # Unified workflow technical documentation
        └── model/
            ├── app.py         # Unified 5-Screen Kivy Desktop Application
            ├── config.py      # Master configuration & non-colliding sys.path injector
            ├── orchestrator.py # Master 4-stage pipeline execution coordinator
            ├── sample_data.py # Demo testing data provider (Arjun Sharma + DataFlow Inc.)
            ├── sample_jd.txt  # Demo job description text file
            ├── sample_resume.txt # Demo resume text file
            └── voice_engine.py # Stage 3 adapter with dynamic system prompt injection
```

---

## 📄 Key Directory Descriptions

### 1. `backend/` (Root Directory)
- **`.env`**: Stores sensitive API credentials (`GEMINI_API_KEY`, `TAVILY_API_KEY`, `OLLAMA_MODEL`).
- **`requirements.txt`**: Consolidated dependencies file for the entire backend model suite.
- **`run.bat`**: Interactive Windows Command Prompt launcher providing a 12-choice menu to run individual stage tests or the full workflow app.
- **`scan_code_quality.py`**: Automated audit script ensuring docstring coverage, single requirements.txt usage, and clean directory hygiene.

### 2. `backend/doc/`
- Contains system-level documentation covering the complete backend architecture (`current.md`) and directory structure (`folder_strucuture.md`).

### 3. `backend/model/`
- Contains all AI model subsystems organized cleanly into `research_model`, `question_model`, `voice_to_voice_model`, `reports_model`, and `workflow`.
- Includes `overall_model_process.md` detailing the complete high-level process matrix.

### 4. `backend/model/sessions/`
- Output directory storing timestamped session folders (`sess_<timestamp>/`) containing all generated artifacts (`interview_questions.json`, `system_prompt.txt`, `continuous_mic_input.wav`, `session_manifest.json`, `turn_XX.wav`, `report.json`, `evaluation_summary.md`).
