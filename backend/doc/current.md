# Netran AI Backend — Current System Architecture & Implementation Status

**Status:** ✅ **COVERED & OPERATIONAL** (All 4 Stages + Unified Workflow Orchestrator Complete)  
**Last Updated:** July 26, 2026  
**Root Path:** `backend/`  

---

## 📌 Executive Summary

Netran AI (SAMWINI) is an intelligent, multimodal AI technical interviewer. The backend is structured into **four core model stages** linked together by a **unified workflow orchestrator**:

1. **Stage 1 (Research Model):** Web-augmented Job Description analysis and market intelligence search.
2. **Stage 2 (Question Engine):** Candidate resume parsing, skill gap matrix calculation, and 15-question tree generation.
3. **Stage 3 (Voice-to-Voice Loop):** Real-time cascaded voice interaction (VAD + STT + Streaming LLM + Neural TTS) with continuous mic recording.
4. **Stage 4 (Reports Engine):** Non-destructive audio slicing and 3-branch Gemini multimodal evaluation to synthesize candidate hiring reports.
5. **Workflow Orchestrator:** Unified 5-screen Kivy desktop GUI application integrating Stage 1 → Stage 2 → Stage 3 → Stage 4 seamlessly.

---

## 📊 Summary Matrix: Subsystem Status

| Stage | Module Name | Status | Location | Key Technologies & Output |
|---|---|---|---|---|
| **Stage 1** | `research_model` | ✅ **Covered** | `backend/model/research_model/model/` | Gemini 3.6 Flash, Tavily Search API, SQLite caching (`cache.db`), Kivy UI |
| **Stage 2** | `question_model` | ✅ **Covered** | `backend/model/question_model/model/` | `pypdf`, `python-docx`, Gemini 3.6 Flash, Kivy GUI (`front.py`), `interview_questions.json`, `interviewer_behavior.json` |
| **Stage 3** | `voice_to_voice_model` | ✅ **Covered** | `backend/model/voice_to_voice_model/model/` | Silero VAD v3, Faster-Whisper int8, Ollama Qwen2.5:1.5b, Kokoro-82M TTS. Per-frame DC offset + auto-gain (up to 50x) applied before `ContinuousMicWriter` write AND Whisper STT. ~900ms silence endpointing. `⚡ Done Speaking` button. `test/input/` & `test/output/sess_<timestamp>/` I/O contract. |
| **Stage 4** | `reports_model` | ✅ **Covered** | `backend/model/reports_model/model/` | Audio slicing (`wave`), Gemini 3-branch multimodal evaluation, `report.json`, `evaluation_summary.md`, Kivy GUI (`front.py`) |
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
│  STAGE 3: Voice Interview (workflow/model/voice_engine.py)                 │
│  • Overrides Ollama persona with dynamic system_prompt.txt                  │
│  • Silero VAD + Faster-Whisper STT + Qwen2.5 LLM + Kokoro TTS              │
│  • Auto-stops after 15 questions                                            │
│  • Output: continuous_mic_input.wav & session_manifest.json                 │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Reports Engine (reports_model/model/report_builder.py)           │
│  • Slices turn_XX.wav clips -> Gemini 3-Branch Multimodal Evaluation        │
│  • Output: report.json & evaluation_summary.md                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Subsystem Breakdown

### 1. Stage 1: Research Model (`research_model`)
- **Location**: `backend/model/research_model/model/`
- **Core Files**: `pipeline.py`, `jd_parser.py`, `search_engine.py`, `rubric_generator.py`, `cache.py`, `gemini_client.py`, `schemas.py`, `front.py`
- **Functionality**: Extracts role requirements from JD text, performs Tavily web search filtered to trusted domains (`leetcode.com`, `glassdoor.com`, `github.com`, `geeksforgeeks.org`, `reddit.com`), synthesizes an assessment rubric using Gemini 3.6 Flash, and caches results in `cache.db` for instant re-runs (< 1s).

### 2. Stage 2: Question Engine (`question_model`)
- **Location**: `backend/model/question_model/model/`
- **Core Files**: `front.py`, `cache.py`, `question_generator.py`, `prompt_builder.py`, `resume_parser.py`, `schemas.py`, `config.py`, `test_pipeline.py`
- **Functionality**: Ingests candidate resume (`.pdf`, `.docx`, `.txt`, `.json`) and JD text. Performs skill gap analysis to construct a 15-question tree stratified across 3 difficulty tiers (Junior, Mid, Senior) and builds a custom 1-2 sentence latency-constrained system prompt for Stage 3's voice interviewer (`Eva`). Caches generated results in SQLite `cache.db` for instant re-runs (<1ms). Outputs `interview_questions.json` and `interviewer_behavior.json` inside session folder `sess_<timestamp>/`.

### 3. Stage 3: Voice-to-Voice Model (`voice_to_voice_model`)
- **Location**: `backend/model/voice_to_voice_model/model/`
- **Core Files**: `listener.py`, `brain.py`, `speaker.py`, `session_logger.py`, `benchmark.py`, `download_vad.py`, `front.py`
- **Functionality**: Drives the real-time cascaded voice loop. Uses Silero VAD v3 + dynamic peak auto-gain for robust speech detection, Faster-Whisper (`small` int8) for STT, Ollama `qwen2.5:1.5b` for LLM reasoning, Kokoro-82M (`af_bella`) for neural TTS streaming, and logs raw continuous PCM mic audio alongside a millisecond-precision timing manifest.

### 4. Stage 4: Reports Model (`reports_model`)
- **Location**: `backend/model/reports_model/model/`
- **Core Files**: `audio_slicer.py`, `gemini_evaluator.py`, `report_builder.py`, `report_schema.py`, `front.py`, `test_pipeline.py`
- **Functionality**: Post-interview analytics module. Uses Python `wave` to cut non-destructive turn audio clips (`turn_01.wav` ... `turn_15.wav`) based on manifest timestamps, runs a 3-branch Gemini multimodal evaluation (Audio Branch, Technical Branch, Combine Branch), and generates `report.json` and `evaluation_summary.md`.

### 5. Workflow Orchestrator (`workflow`)
- **Location**: `backend/model/workflow/model/`
- **Core Files**: `front.py`, `orchestrator.py`, `voice_engine.py`, `config.py`, `sample_data.py`, `test_pipeline.py`
- **Functionality**: Master multi-stage controller. Houses the unified 5-screen Kivy desktop GUI application (`SetupScreen`, `ResearchScreen`, `QuestionScreen`, `InterviewScreen`, `ReportScreen`), orchestrates background pipeline threads, and provides built-in demo testing data.

---

## 🛠️ Code Quality, Hygiene & Verification

1. **Unified Requirements Management**:
   - Single master [`backend/requirements.txt`](file:///c:/kali/product/netran%20ai/backend/requirements.txt) file at the root. Per-stage requirements files have been removed.

2. **Automated Audit Scanner**:
   - [`scan_code_quality.py`](file:///c:/kali/product/netran%20ai/backend/scan_code_quality.py) verifies docstring coverage, file hygiene, and single requirements file enforcement across all 34 Python files.

3. **Isolated Test & Workflow Storage**:
   - Standalone stage test executions save output locally inside `<stage>/model/test_output/`.
   - Unified workflow runs store middle process data in `model/workflow/test/process/sess_<timestamp>/` and final reports in `model/workflow/test/output/sess_<timestamp>/`.

4. **Interactive Batch Launcher**:
   - Root [`run.bat`](file:///c:/kali/product/netran%20ai/backend/run.bat) provides an interactive Command Prompt menu to launch the full workflow, execute stage tests, or clean test data.
