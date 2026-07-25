# Netran AI: Overall Model Process & Pipeline Architecture

This document tracks the multi-stage AI pipeline components implemented inside the `backend/model/` directory, detailing the technical specification, operational status, and inter-stage data flow across all 4 interview stages and the unified workflow orchestrator.

---

## 📌 High-Level Architecture Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   STAGE 1: RESEARCH                                    │
│                     backend/model/research_model/model/  [COVERED]                     │
│  - JD Parsing & Query Formulation (jd_parser.py)                                       │
│  - Web Intelligence Search via Tavily API (search_engine.py)                           │
│  - Gemini 3.6 Flash Rubric Generator (rubric_generator.py)                             │
│  - SQLite Hashed Rubric Caching (cache.py)                                             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Interview Rubric (in-memory)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               STAGE 2: QUESTION ENGINE                                 │
│                     backend/model/question_model/model/  [COVERED]                     │
│  - Resume Parsing via pypdf / python-docx (resume_parser.py)                           │
│  - Skill Overlap & Gap Matrix Calculation                                              │
│  - Gemini 3.6 Flash Tiered 15-Question Tree Generator (interview_questions.json)       │
│  - Latency-Constrained Behavioral System Prompt Builder (system_prompt.txt)            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Question Tree & Persona Prompt
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               STAGE 3: VOICE-TO-VOICE LOOP                             │
│                   backend/model/voice_to_voice_model/model/  [COVERED]                 │
│  - Silero VAD v3 + Auto-Gain Peak Normalizer + Faster-Whisper STT (listener.py)        │
│  - Local Ollama Qwen2.5:1.5B Interviewer Persona Engine (brain.py)                     │
│  - Kokoro-82M Neural TTS Direct 24kHz Audio Streaming (speaker.py)                     │
│  - Asynchronous PCM Mic Recording -> continuous_mic_input.wav (listener.py)            │
│  - Monotonic Timestamp Telemetry -> session_manifest.json (session_logger.py)          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Session Artifacts (backend/model/sessions/<id>/)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                STAGE 4: REPORT ENGINE                                  │
│                      backend/model/reports_model/model/  [COVERED]                     │
│  - Non-Destructive Audio Slicer per Turn (audio_slicer.py)                             │
│  - Gemini 3.6 Flash Multimodal 3-Branch Evaluator (gemini_evaluator.py)                │
│  - Pydantic Schema Payload Validation (report_schema.py)                               │
│  - Dual Artifact Generator: report.json & evaluation_summary.md (report_builder.py)    │
│  - Kivy Desktop Test UI & Headless CLI Runner (test_ui.py / test_pipeline.py)          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Summary Matrix: Subsystem Operational Status

| Stage | Module Name | Status | Location | Key Deliverables & Output |
|---|---|---|---|---|
| **Stage 1** | `research_model` | ✅ **Covered** | `backend/model/research_model/model/` | JD parsing, Tavily domain web search, Gemini rubric generator, SQLite cache (`cache.db`), Kivy UI |
| **Stage 2** | `question_model` | ✅ **Covered** | `backend/model/question_model/model/` | PDF/DOCX/TXT resume parsing, skill gap matrix, Gemini 15-question tree (`interview_questions.json`) & system prompt (`system_prompt.txt`) |
| **Stage 3** | `voice_to_voice_model` | ✅ **Covered** | `backend/model/voice_to_voice_model/model/` | Silero VAD, Faster-Whisper int8, Ollama Qwen2.5 LLM, Kokoro TTS, `continuous_mic_input.wav`, `session_manifest.json` |
| **Stage 4** | `reports_model` | ✅ **Covered** | `backend/model/reports_model/model/` | Audio slicing (`wave`), 3-branch Gemini multimodal evaluation, `report.json` & `evaluation_summary.md` synthesis, Kivy UI |
| **Workflow** | `workflow` | ✅ **Covered** | `backend/model/workflow/model/` | Master 5-screen Kivy UI orchestrator linking Stage 1 → Stage 2 → Stage 3 → Stage 4 seamlessly |

---

## 🔍 Detailed Component Breakdown

### Stage 1: Research Model (`research_model`)
* **Status**: ✅ **COVERED & OPERATIONAL**
* **Location**: `backend/model/research_model/model/`
* **Implemented Code**:
  - `app.py`: Kivy desktop GUI dashboard for JD text input/file upload and live research execution.
  - `jd_parser.py`: Evaluates raw JD text via Gemini 3.6 Flash to extract role title, target company, core tech stack, and targeted search queries.
  - `search_engine.py`: Tavily Search API integration with domain whitelisting (`leetcode.com`, `glassdoor.com`, `github.com`, `geeksforgeeks.org`, `reddit.com`).
  - `gemini_client.py`: Gemini 3.6 Flash Interactions API client with REST fallback.
  - `rubric_generator.py`: Synthesizes raw JD and live web context into a structured `InterviewRubric`.
  - `cache.py`: SQLite hashing engine (`cache.db`) for caching rubrics by SHA-256 hash of input JD text.
  - `schemas.py`: Pydantic data schemas (`ParsedJD`, `InterviewTopic`, `InterviewRubric`).

---

### Stage 2: Question Model (`question_model`)
* **Status**: ✅ **COVERED & OPERATIONAL**
* **Location**: `backend/model/question_model/model/`
* **Implemented Code**:
  - `resume_parser.py`: PDF (`pypdf`), DOCX (`python-docx`), and TXT document extractor.
  - `schemas.py`: Pydantic v2 schemas (`Stage2Output`, `QuestionItem`) for structured question tree and system prompt.
  - `prompt_builder.py`: System prompt constraint compiler enforcing latency limits (1-2 sentences) and probing strategy for Stage 3 `brain.py`.
  - `question_generator.py`: Core reasoning engine utilizing Gemini 3.6 Flash with structured Pydantic schema outputs.
  - `test_pipeline.py`: Automated CLI testing harness with dummy resume generator.
* **Output Artifacts**:
  - `interview_questions.json` (Saved to `backend/model/sessions/<session_id>/`)
  - `system_prompt.txt` (Saved to `backend/model/sessions/<session_id>/`)

---

### Stage 3: Voice-to-Voice Model (`voice_to_voice_model`)
* **Status**: ✅ **COVERED & OPERATIONAL**
* **Location**: `backend/model/voice_to_voice_model/model/`
* **Implemented Code**:
  - `main_app.py`: Kivy Desktop UI, streaming regex sentence buffer, live conversation panel, dual modes (LLM vs. Script Calibration).
  - `listener.py`: Silero VAD v3 ONNX + Faster-Whisper (`small` int8 CPU) + Echo Gate + `ContinuousMicWriter` background thread writing raw 16kHz WAV.
  - `brain.py`: Ollama `qwen2.5:1.5b` local streaming LLM engine (`Eva` persona).
  - `speaker.py`: Kokoro-82M neural TTS (`af_bella` voice) with direct `sounddevice` float32 streaming playback.
  - `session_logger.py`: High-resolution monotonic timer (`time.perf_counter()`) logging per-turn millisecond offsets and outputting `session_manifest.json`.
  - `benchmark.py`: Latency performance telemetry (`stt_ms`, `ttft_ms`, `ttfa_ms`) saved to `benchmark_log.csv`.
* **Output Artifacts**:
  - `continuous_mic_input.wav` (Saved to `backend/model/sessions/<session_id>/`)
  - `session_manifest.json` (Saved to `backend/model/sessions/<session_id>/`)

---

### Stage 4: Reports Model (`reports_model`)
* **Status**: ✅ **COVERED & OPERATIONAL**
* **Location**: `backend/model/reports_model/model/`
* **Implemented Code**:
  - `report_schema.py`: Pydantic v2 schemas (`CandidateReportPayload`, `TurnAnalysis`, `PillarScore`, `AudioBranchOutput`, `TechnicalBranchOutput`).
  - `audio_slicer.py`: Non-destructive WAV slicing utility using standard Python `wave` module to extract turn audio clips based on `session_manifest.json` timing telemetry.
  - `gemini_evaluator.py`: 3-stage Gemini multimodal evaluation engine using Gemini 3.6 Flash (Audio Branch, Technical Branch, Combine Synthesis Branch).
  - `report_builder.py`: Pipeline orchestrator running audio slicing and evaluation branches to render dual output artifacts (`report.json` and `evaluation_summary.md`).
  - `test_pipeline.py`: Headless CLI test runner.
  - `test_ui.py`: Kivy desktop GUI application.
* **Output Artifacts**:
  - `report.json` (Saved to `backend/model/sessions/<session_id>/`)
  - `evaluation_summary.md` (Saved to `backend/model/sessions/<session_id>/`)
  - `turn_XX.wav` (Saved to `backend/model/sessions/<session_id>/`)

---

### Workflow Orchestrator (`workflow`)
* **Status**: ✅ **COVERED & OPERATIONAL**
* **Location**: `backend/model/workflow/model/`
* **Implemented Code**:
  - `app.py`: Kivy Desktop UI application with 5-phase ScreenManager (`SetupScreen` → `ResearchScreen` → `QuestionScreen` → `InterviewScreen` → `ReportScreen`).
  - `orchestrator.py`: Master pipeline coordinator executing Stage 1 → Stage 2 → Stage 3 → Stage 4 in background threads with live UI progress callbacks.
  - `voice_engine.py`: Stage 3 voice loop adapter that injects Stage 2 dynamic prompt (`system_prompt.txt`) into Ollama Qwen2.5 persona and auto-stops after 15 questions.
  - `config.py`: Unified `.env` configuration and non-colliding module path injector.
  - `sample_data.py`: Built-in demo testing harness with sample resume (`sample_resume.txt`) and JD (`sample_jd.txt`).
* **Root Suite Launcher**:
  - Root [`run.bat`](file:///c:/kali/product/netran%20ai/backend/run.bat): Interactive Windows Command Prompt launcher providing a 17-choice menu for workflow execution, stage testing, setup, code auditing, and deep data cleaning.

---

## 🛡️ Quality Assurance & Environment Standards

1. **Unified Requirements**:
   - Single master [`requirements.txt`](file:///c:/kali/product/netran%20ai/backend/requirements.txt) at `backend/` root.
2. **Automated Audit Scanner**:
   - [`scan_code_quality.py`](file:///c:/kali/product/netran%20ai/backend/scan_code_quality.py) enforces 100% module docstring coverage and directory hygiene across all 34 Python files.
3. **Test Data Isolation**:
   - Standalone stage test executions output to `<stage>/model/test_output/`.
   - Unified workflow runs save session artifacts to `backend/model/sessions/sess_<timestamp>/`.
