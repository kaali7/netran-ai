# Netran AI Backend — Current System Architecture & Implementation Status

**Status:** ✅ **COVERED & OPERATIONAL (MVP Phase Complete)**  
**Root Path:** `backend/`  

---

## 📌 Executive Summary

Netran AI is an intelligent, multimodal AI technical interviewer. The backend is structured into **four core model stages** linked together by a **unified workflow orchestrator**, now successfully completing its MVP phase.

1. **Stage 1 (Research Model):** Web-augmented Job Description analysis and market intelligence search.
2. **Stage 2 (Question Engine):** Candidate resume parsing, skill gap matrix calculation, and 15-question tree generation.
3. **Stage 3 (Voice-to-Voice Loop):** Real-time cascaded voice interaction (VAD + STT + Streaming LLM + Neural TTS) utilizing local Qwen2.5:3B reasoning, Kokoro-82M TTS, and a hybrid turn-taking classifier (Tier 1 Regex + Tier 2 Ollama `OLLAMA_MODEL`, qwen2.5:3b by default).
4. **Stage 4 (Reports Engine):** Non-destructive audio slicing, precision telemetry extraction, and 3-branch Gemini multimodal evaluation.

---

## 📊 Summary Matrix: Subsystem Status

| Stage | Module Name | Status | Key Technologies & Output |
|---|---|---|---|
| **Stage 1** | `research_model` | ✅ **Covered** | Gemini 3.6 Flash, Tavily API, SQLite caching |
| **Stage 2** | `question_model` | ✅ **Covered** | Gemini 3.6 Flash, `pypdf`, `python-docx`. Output: `interview_questions.json`, `interviewer_behavior.json`, `resume_analysis.json` |
| **Stage 3** | `voice_to_voice_model` | ✅ **Covered** | Silero VAD v3, Faster-Whisper int8, Ollama Qwen2.5:3b, Kokoro-82M TTS, Hybrid Turn Classifier (Tier 1 Regex + Tier 2 Ollama OLLAMA_MODEL). Output: `recording.wav`, `transcript.json` |
| **Stage 4** | `reports_model` | ✅ **Covered** | Audio slicing, Gemini 3-branch evaluation (Audio/Tech/Comb) with RateLimit retry. Output: `report.json`, `evaluation_summary.md` |
| **Workflow** | `workflow` | ✅ **Covered** | Master pipeline coordinator (`orchestrator.py`), 6-screen Kivy UI |

---

## 🏗️ System Architecture & Stage Handoff Chain

```text
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
│  • Output: InterviewRubric object (in-memory/cached)                        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Question Engine (question_model/model/pipeline.py)                │
│  • Output: interview_questions.json, interviewer_behavior.json (incl.       │
│    whisper_domain_vocabulary), resume_analysis.json                         │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ (Handoff: Vocabulary & Resume Anchors injected into STT & LLM)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Voice Interview (voice_to_voice_model/model/pipeline.py)          │
│  • Ingests Stage 2 artifacts to boost Whisper STT and ground the LLM prompt.│
│  • Voice Loop: VAD -> STT -> Qwen2.5:3B LLM -> Kokoro TTS                   │
│  • Hybrid Turn Classifier: Evaluates interruptions using Ollama `OLLAMA_MODEL` (qwen2.5:3b by default) │
│  • Output: recording.wav & transcript.json                                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Reports Engine (reports_model/model/pipeline.py)                  │
│  • Ingests recording.wav + transcript.json + Context                        │
│  • Output: report.json & evaluation_summary.md                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Subsystem Breakdown

### 1. Stage 1: Research Model (`research_model`)
- **Location**: `backend/model/research_model/model/`
- **Core Files:** `pipeline.py`, `jd_parser.py`, `search_engine.py`, `rubric_generator.py`, `cache.py`, `gemini_client.py`, `schemas.py`, `front.py`, `test_pipeline.py`.
- **Functionality**: Extracts role requirements from JD text, performs Tavily web search filtered to trusted domains, synthesizes an assessment rubric using Gemini 3.6 Flash, and caches results in `cache.db` for instant re-runs (< 1s).

### 2. Stage 2: Adaptive Question Engine (`question_model`)
- **Location**: `backend/model/question_model/model/`
- **Core Files:** `front.py`, `cache.py`, `pipeline.py`, `question_generator.py`, `prompt_builder.py`, `prompts.py`, `resume_parser.py`, `schemas.py`, `config.py`, `test_pipeline.py`.
- **Functionality**: Ingests candidate resume and JD text or Stage 1 Market Intelligence outputs. Synthesizes candidate skill match matrices, constructs a 15-question holistic interview tree, and embeds Eva's latency-constrained system prompt alongside a custom `whisper_domain_vocabulary` (for STT enhancement) inside `interviewer_behavior.json`. Outputs `resume_analysis.json`, `interview_questions.json`, and `interviewer_behavior.json`.

### 3. Stage 3: Voice-to-Voice Model (`voice_to_voice_model`)
- **Location**: `backend/model/voice_to_voice_model/model/`
- **Core Files:** `pipeline.py`, `voice_engine.py`, `listener.py`, `brain.py`, `speaker.py`, `turn_classifier.py`, `session_logger.py`, `benchmark.py`, `question_manager.py`, `schemas.py`, `download_vad.py`, `front.py`.
- **Functionality**: Drives the real-time cascaded voice loop under 100% offline model resolution (`HF_HUB_OFFLINE=1`). Uses Silero VAD v3 + dynamic peak auto-gain. Faster-Whisper (`small` int8) handles STT (dynamically weighted with candidate-specific resume jargon), Ollama `qwen2.5:3b` manages LLM reasoning, and Kokoro-82M executes neural TTS. Includes hybrid turn classifier leveraging Ollama `OLLAMA_MODEL` (qwen2.5:3b by default, aligned with brain.py). Logs gain-boosted continuous PCM mic audio (`recording.wav`) alongside a millisecond-precision timing manifest (`transcript.json`).

### 4. Stage 4: Reports Model (`reports_model`)
- **Location**: `backend/model/reports_model/model/`
- **Core Files:** `audio_slicer.py`, `config.py`, `gemini_evaluator.py`, `pipeline.py`, `prompts.py`, `report_builder.py`, `report_schema.py`, `schemas.py`, `front.py`, `test_pipeline.py`.
- **Functionality**: Post-interview analytics module. Slices non-destructive turn audio clips, ingests Stage 1 rubric and resume grounding context, runs a 3-branch Gemini multimodal evaluation with automatic 429 RateLimit exponential backoff retry. Outputs `report.json` and `evaluation_summary.md`.

### 5. Workflow Orchestrator (`workflow`)
- **Location**: `backend/model/workflow/model/`
- **Core Files**: `front.py`, `orchestrator.py`, `config.py`, `sample_data.py`, `test_pipeline.py`
- **Functionality**: Master multi-stage controller. Houses the unified 6-screen Kivy desktop GUI application, orchestrates background pipeline threads, and provides built-in demo testing data.

---

## 🛠️ Code Quality, Hygiene & Verification

1. **Unified Requirements Management**:
   - Single master `backend/requirements.txt` file at the root.

2. **Automated Audit Scanner**:
   - `scan_code_quality.py` verifies docstring coverage, file hygiene, and single requirements file enforcement across all Python files.

3. **Isolated Test & Workflow Storage**:
   - Standalone stage test executions save output strictly inside `<stage>/test/output/sess_<timestamp>/`.
   - Unified workflow runs store middle process data in `model/workflow/test/process/sess_<timestamp>/` and final reports in `model/workflow/test/output/sess_<timestamp>/`.

4. **Interactive Batch Launcher**:
   - Root `run.bat` provides an interactive Command Prompt menu to launch the full workflow, execute stage tests, or clean test data.

---

## 🚀 Next Steps (Phase 2 Roadmap)
1. **Web Engine Transition:** Migrate away from the Kivy Desktop GUI to a modern web-based UI.
2. **FastAPI WebSockets:** Implement bidirectional WebSocket streaming to handle real-time VAD events, partial STT transcripts, and LLM text generation between the Python backend and the frontend.
3. **Next.js UI Integration:** Develop the web frontend using Next.js/React, adopting the premium dark mode aesthetic (glassmorphism, vibrant tags) previously established in the Kivy app.
