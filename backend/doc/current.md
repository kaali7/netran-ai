# Netran AI Backend — Current System Architecture & Implementation Status

**Status:** ✅ **COVERED & OPERATIONAL** (All 4 Stages + Unified Workflow Orchestrator Complete)  
**Last Updated:** August 01, 2026  
**Root Path:** `backend/`  

---

## 📌 Executive Summary

Netran AI is an intelligent, multimodal AI technical interviewer. The backend is structured into **four core model stages** linked together by a **unified workflow orchestrator**:

1. **Stage 1 (Research Model):** Web-augmented Job Description analysis and market intelligence search.
2. **Stage 2 (Question Engine):** Candidate resume parsing, skill gap matrix calculation, and 15-question tree generation.
3. **Stage 3 (Voice-to-Voice Loop):** Real-time cascaded voice interaction (VAD + STT + Streaming LLM + Neural TTS) with multi-screen Kivy GUI, preset loader, selectable question limit spinner, output history inspector, and WAV audio player.
4. **Stage 4 (Reports Engine):** Non-destructive audio slicing, precision Stage 3 telemetry extraction, and 3-branch Gemini multimodal evaluation with 429 RateLimit retry to synthesize executive candidate hiring reports.
5. **Workflow Orchestrator:** Unified 5-screen Kivy desktop GUI application integrating Stage 1 → Stage 2 → Stage 3 → Stage 4 seamlessly.

---

## 📊 Summary Matrix: Subsystem Status

| Stage | Module Name | Status | Location | Key Technologies & Output |
|---|---|---|---|---|
| **Stage 1** | `research_model` | ✅ **Covered** | `backend/model/research_model/model/` | Gemini 3.6 Flash, Tavily Search API, SQLite caching (`cache.db`), Kivy UI |
| **Stage 2** | `question_model` | ✅ **Covered** | `backend/model/question_model/model/` | `pypdf`, `python-docx`, Gemini 3.6 Flash, Kivy GUI (`front.py`), `interview_questions.json`, `interviewer_behavior.json`, `resume_analysis.json`, `system_prompt.txt` |
| **Stage 3** | `voice_to_voice_model` | ✅ **Covered** | `backend/model/voice_to_voice_model/model/` | Silero VAD v3, Faster-Whisper int8, Ollama Qwen2.5:3b, Kokoro-82M TTS. 100% offline local model resolution (`HF_HUB_OFFLINE=1`). Per-frame DC offset + auto-gain before WAV write AND Whisper STT. Clause-Level Streaming for sub-250ms TTFA, Persistent PyAudio output stream. Multi-screen Kivy GUI (`ScreenManager`) with premium dark theme, top history action bar, selectable question limit (5, 10, 15, All), full-page output inspector, audio playback engine with progress bar (`0:15 / 1:30`), pixel-perfect wrapped text layout, and 4-button control bar. Session outputs saved in `test/output/sess_<timestamp>/` as `transcript.json` and `recording.wav`. |
| **Stage 4** | `reports_model` | ✅ **Covered** | `backend/model/reports_model/model/` | Audio slicing (`wave`), Gemini 3-branch multimodal evaluation, 429 RateLimit exponential backoff retry, `TurnTelemetry`, `BehavioralFlag`, `CandidateFeedback` roadmap, `transcript.json` resolution, `report.json`, `evaluation_summary.md`, Kivy GUI (`front.py`) with interactive input/output selectors |
| **Workflow** | `workflow` | ✅ **Covered** | `backend/model/workflow/model/` | Master pipeline coordinator (`orchestrator.py`), 5-screen Kivy Desktop App (`front.py`), demo data testing harness |

---

## 🏗️ System Architecture & Stage Handoff Chain

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SetupScreen (Kivy UI / front.py)                                           │
│  • Candidate Metadata & Seniority Selector                                  │
│  • Dual JD Input: Paste text  OR  Upload File (PDF/DOCX/TXT)                │
│  • Resume File Upload (PDF/DOCX/TXT)                                        │
│  • "🎯 Use Demo Data" button (Arjun Sharma + DataFlow Inc.)                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Research Model (research_model/model/pipeline.py)                 │
│  • Checks SQLite Cache (SHA-256 hash) -> Tavily Web Search -> Gemini Rubric │
│  • Output: InterviewRubric object (in-memory)                               │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Question Engine (question_model/model/question_generator.py)     │
│  • Parsed Resume + JD -> 15-question tree & dynamic system prompt           │
│  • Output: interview_questions.json & system_prompt.txt                     │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Voice Interview (voice_to_voice_model/model/front.py)             │
│  • Ingests Stage 2 bundle (interview_questions.json, system_prompt.txt)     │
│  • Silero VAD + Faster-Whisper STT + Qwen2.5:3B LLM + Kokoro TTS (Offline)  │
│  • Clause-Level Streaming & Persistent PyAudio for 0ms overhead            │
│  • Selectable question limit spinner (5, 10, 15, All)                       │
│  • Full-page history inspector with interactive audio playback engine       │
│  • Output: recording.wav & transcript.json                                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Reports Engine (reports_model/model/pipeline.py)                  │
│  • Ingests recording.wav + transcript.json + Resume/Rubric context          │
│  • Slices turn_XX.wav clips -> Gemini 3-Branch Evaluation (Audio/Tech/Comb) │
│  • Extracts TurnTelemetry & programmatically detects STT Hallucination flags │
│  • Generates Behavioral Red Flags & Candidate Upskilling Roadmap            │
│  • Auto-retries RateLimit 429 errors with exponential backoff               │
│  • Output: report.json & evaluation_summary.md (in test/output/sess_.../)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Subsystem Breakdown

### 1. Stage 1: Research Model (`research_model`)
- **Location**: `backend/model/research_model/model/`
- **Core Files**: `pipeline.py`, `jd_parser.py`, `search_engine.py`, `rubric_generator.py`, `cache.py`, `gemini_client.py`, `schemas.py`, `front.py`
- **Functionality**: Extracts role requirements from JD text, performs Tavily web search filtered to trusted domains (`leetcode.com`, `glassdoor.com`, `github.com`, `geeksforgeeks.org`, `reddit.com`), synthesizes an assessment rubric using Gemini 3.6 Flash, and caches results in `cache.db` for instant re-runs (< 1s).

### 2. Stage 2: Adaptive Question Engine (`question_model`)
- **Location**: `backend/model/question_model/model/`
- **Core Files**: `front.py`, `cache.py`, `pipeline.py`, `question_generator.py`, `prompt_builder.py`, `resume_parser.py`, `schemas.py`, `config.py`, `test_pipeline.py`
- **Functionality**: Ingests candidate resume (`.pdf`, `.docx`, `.txt`, `.json`) and JD text or Stage 1 Market Intelligence outputs (`stage1_output.json`). Synthesizes candidate skill match matrices (`matched_skills`, `missing_or_gap_skills`, `resume_red_flags`, `key_projects_to_probe`), constructs a 15-question branching tree with evaluation rubrics and 2-way follow-ups, and builds Eva's latency-constrained system prompt. Caches generated results in SQLite `cache.db` for instant re-runs. Outputs `resume_analysis.json`, `interview_questions.json`, `interviewer_behavior.json`, and `system_prompt.txt` inside session folder `sess_<timestamp>/`.

### 3. Stage 3: Voice-to-Voice Model (`voice_to_voice_model`)
- **Location**: `backend/model/voice_to_voice_model/model/`
- **Core Files**: `listener.py`, `brain.py`, `speaker.py`, `session_logger.py`, `benchmark.py`, `question_manager.py`, `schemas.py`, `download_vad.py`, `front.py`
- **Functionality**: Drives the real-time cascaded voice loop under 100% offline model resolution (`HF_HUB_OFFLINE=1`). Uses Silero VAD v3 + dynamic peak auto-gain for robust speech detection, Faster-Whisper (`small` int8) for STT, Ollama `qwen2.5:3b` for LLM reasoning, Kokoro-82M (`af_bella`) for neural TTS streaming (via Persistent PyAudio & Clause-Level streaming), and logs gain-boosted continuous PCM mic audio (`recording.wav`) alongside a millisecond-precision timing manifest (`transcript.json`). Features premium dark-themed multi-screen Kivy GUI with preset ingestion, selectable question limits, full-page history inspector, interactive audio playback engine with progress tracking, and non-overlapping controls.

### 4. Stage 4: Reports Model (`reports_model`)
- **Location**: `backend/model/reports_model/model/`
- **Core Files**: `audio_slicer.py`, `config.py`, `gemini_evaluator.py`, `pipeline.py`, `prompts.py`, `schemas.py`, `front.py`, `test_pipeline.py`
- **Functionality**: Post-interview analytics module. Uses Python `wave` to cut non-destructive turn audio clips (`turn_01.wav` ... `turn_15.wav`) based on manifest timestamps, ingests Stage 1 rubric and resume grounding context, runs a 3-branch Gemini multimodal evaluation (Audio Branch, Technical Branch, Combine Branch) with automatic 429 RateLimit exponential backoff retry, extracts deterministic `TurnTelemetry` (`initial_silence_latency_ms`, `turn_duration_sec`, `stt_whisper_hallucination_flag`), surfaces `BehavioralFlag` red flags and `CandidateFeedback` upskilling roadmaps, and generates `report.json` and `evaluation_summary.md` exclusively inside `test/output/sess_<timestamp>/`. Features interactive Kivy Desktop GUI (`front.py`) with input session picker and saved output artifact selector.

### 5. Workflow Orchestrator (`workflow`)
- **Location**: `backend/model/workflow/model/`
- **Core Files**: `front.py`, `orchestrator.py`, `voice_engine.py`, `config.py`, `sample_data.py`, `test_pipeline.py`
- **Functionality**: Master multi-stage controller. Houses the unified 5-screen Kivy desktop GUI application (`SetupScreen`, `ResearchScreen`, `QuestionScreen`, `InterviewScreen`, `ReportScreen`), orchestrates background pipeline threads, and provides built-in demo testing data.

---

## 🛠️ Code Quality, Hygiene & Verification

1. **Unified Requirements Management**:
   - Single master [`backend/requirements.txt`](file:///c:/kali/product/netran%20ai/backend/requirements.txt) file at the root. Per-stage requirements files have been removed.

2. **Automated Audit Scanner**:
   - [`scan_code_quality.py`](file:///c:/kali/product/netran%20ai/backend/scan_code_quality.py) verifies docstring coverage, file hygiene, and single requirements file enforcement across all Python files.

3. **Isolated Test & Workflow Storage**:
   - Standalone stage test executions save output strictly inside `<stage>/test/output/sess_<timestamp>/`.
   - Unified workflow runs store middle process data in `model/workflow/test/process/sess_<timestamp>/` and final reports in `model/workflow/test/output/sess_<timestamp>/`.

4. **Interactive Batch Launcher**:
   - Root [`run.bat`](file:///c:/kali/product/netran%20ai/backend/run.bat) provides an interactive Command Prompt menu to launch the full workflow, execute stage tests, or clean test data.
