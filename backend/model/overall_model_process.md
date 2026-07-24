# Netran AI: Overall Model Process & Pipeline Architecture

This document tracks the multi-stage AI pipeline components implemented inside the `backend/model/` directory, detailing what stages are **Covered (Completed)** and what stages are **Remaining (Planned)**.

---

## 📌 High-Level Architecture Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   STAGE 1: RESEARCH                                    │
│                     backend/model/research_model/model/  [COVERED]                     │
│  - JD & Resume Parsing (jd_parser.py)                                                  │
│  - Web Intelligence Search (search_engine.py)                                          │
│  - Gemini Rubric & Assessment Matrix Generator (rubric_generator.py)                   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Evaluation Rubric
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               STAGE 2: QUESTION ENGINE                                 │
│                     backend/model/question_model/model/  [REMAINING]                   │
│  - Context-Aware Question Tree Generation                                              │
│  - Resume + JD Keyword Matching & Difficulty Tiering                                   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Structured Question Matrix
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               STAGE 3: VOICE-TO-VOICE LOOP                             │
│                   backend/model/voice_to_voice_model/model/  [COVERED]                 │
│  - Silero VAD v3 + Faster-Whisper STT (listener.py)                                   │
│  - Ollama Qwen2.5:1.5B Interviewer Persona (brain.py)                                  │
│  - Kokoro-82M Neural TTS Streaming (speaker.py)                                        │
│  - Continuous PCM Mic Writer -> continuous_mic_input.wav (listener.py)                 │
│  - Event Timestamp Logger -> session_manifest.json (session_logger.py)                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Session Artifacts (backend/sessions/<id>/)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                STAGE 4: REPORT ENGINE                                  │
│                      backend/model/reports_model/model/  [REMAINING]                   │
│  - Non-Destructive Audio Slicer per Turn (audio_slicer.py)                             │
│  - Acoustic Feature Extractor: WPM, Hesitation, Tremor, Fillers (acoustic_analyzer.py) │
│  - Gemini Dual-Evaluation Candidate Report Generator (evaluator.py)                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Summary Matrix: Covered vs. Remaining Stages

| Stage | Module Name | Status | Location | Key Deliverables |
|---|---|---|---|---|
| **Stage 1** | `research_model` | ✅ **Covered** | `backend/model/research_model/model/` | JD parsing, market web search, Gemini rubric generator, SQLite caching, Kivy UI |
| **Stage 2** | `question_model` | ⏳ **Remaining** | `backend/model/question_model/model/` | Contextual question generation tree, skill matrix mapping |
| **Stage 3** | `voice_to_voice_model` | ✅ **Covered** | `backend/model/voice_to_voice_model/model/` | Silero VAD, Faster-Whisper, Qwen2.5 LLM, Kokoro TTS, Continuous WAV recording, Session Manifest JSON |
| **Stage 4** | `reports_model` | ⏳ **Remaining** | `backend/model/reports_model/model/` | Audio slicing, acoustic & hesitation analysis, Gemini Candidate Report synthesis |
| **Workflow** | `workflow` | ⏳ **Remaining** | `backend/model/workflow/` | End-to-end multi-stage pipeline orchestrator |

---

## 🔍 Detailed Component Breakdown

### Stage 1: Research Model (`research_model`)
* **Status**: ✅ **COVERED & OPERATIONAL**
* **Location**: `backend/model/research_model/model/`
* **Implemented Code**:
  - `app.py`: Kivy desktop GUI dashboard for JD file upload and live analysis execution.
  - `jd_parser.py`: Document text extraction (PDF, DOCX, TXT) and skill keyword extraction.
  - `search_engine.py`: Google Custom Search API & Tavily live search integration for real-time market trends.
  - `gemini_client.py`: Gemini 2.5 Flash API client with structured JSON schema output.
  - `rubric_generator.py`: Generates domain evaluation rubrics and benchmark criteria.
  - `cache.py`: SQLite caching engine (`cache.db`) for search queries and rubrics.
  - `schemas.py`: Pydantic data schemas for structured input/output validation.

---

### Stage 2: Question Model (`question_model`)
* **Status**: ⏳ **REMAINING / PLANNED**
* **Location**: `backend/model/question_model/model/`
* **Planned Code**:
  - Question generation engine combining Stage 1 Rubric + Candidate Resume + Target JD.
  - Question difficulty tiering (Beginner, Intermediate, Advanced).
  - Question script builder outputting structured interview question sets for Stage 3.

---

### Stage 3: Voice-to-Voice Model (`voice_to_voice_model`)
* **Status**: ✅ **COVERED & OPERATIONAL** (Enhanced with Plan B Stage 3 recording & manifest logging)
* **Location**: `backend/model/voice_to_voice_model/model/`
* **Implemented Code**:
  - `main_app.py`: Kivy Desktop UI, streaming sentence buffer, live conversation panel, dual modes (LLM vs. Script Calibration), automatic session folder creation (`backend/sessions/sess_<timestamp>/`).
  - `listener.py`: Silero VAD v3 ONNX + Faster-Whisper (`small` int8 model) + Echo Gate + `ContinuousMicWriter` background thread writing raw 16kHz 16-bit Mono WAV.
  - `brain.py`: Ollama `qwen2.5:1.5b` streaming LLM engine (`Eva` persona).
  - `speaker.py`: Kokoro-82M neural TTS (`af_bella` voice preset) with direct `sounddevice` float32 streaming playback.
  - `session_logger.py`: Monotonic timer (`time.perf_counter()`) logging per-turn millisecond offsets, hesitation gap, latency, and generating `session_manifest.json`.
  - `benchmark.py`: Latency performance telemetry (`stt_ms`, `ttft_ms`, `ttfa_ms`) saved to `benchmark_log.csv`.
* **Output Artifacts**:
  - `backend/sessions/<session_id>/continuous_mic_input.wav`
  - `backend/sessions/<session_id>/session_manifest.json`

---

### Stage 4: Reports Model (`reports_model`)
* **Status**: ⏳ **REMAINING / PLANNED** (Plan B Stage 4)
* **Location**: `backend/model/reports_model/model/`
* **Planned Code**:
  - `audio_slicer.py`: Slices `continuous_mic_input.wav` using sample offsets from `session_manifest.json` into per-question WAV files (`Q1_candidate.wav`, `Q2_candidate.wav`).
  - `acoustic_analyzer.py`: Computes quantitative acoustic metrics (initial hesitation delay, WPM speech velocity, energy tremor/variance, filler word density).
  - `evaluator.py`: Synthesizes Stage 1 Rubric, live transcript, and per-turn acoustic metrics via Gemini 2.5/3.6 Flash using Pydantic JSON schema output (`CandidateReportPayload`).
  - `report_runner.py`: Post-session evaluation orchestrator outputting `candidate_report.json`.

---

### Workflow Orchestrator (`workflow`)
* **Status**: ⏳ **REMAINING / PLANNED**
* **Location**: `backend/model/workflow/`
* **Planned Code**:
  - Unified pipeline coordinator linking Stage 1 → Stage 2 → Stage 3 → Stage 4 into a single seamless interview session lifecycle.
