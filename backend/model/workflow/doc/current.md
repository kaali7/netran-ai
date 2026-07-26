# Unified Interview Workflow Orchestrator — Technical Documentation

**Status:** ✅ **COVERED & OPERATIONAL**  
**Module Location:** `backend/model/workflow/model/`  
**Doc Location:** `backend/model/workflow/doc/`  

---

## 1. Overview & Objective

The **Unified Interview Workflow Orchestrator (`workflow`)** combines all four sub-stages of Netran AI into a single end-to-end application driven by a **5-screen Kivy desktop GUI**:

1. **Stage 1 (Research Model):** Job Description parsing, market intelligence web search (Tavily), and evaluation rubric synthesis (Gemini).
2. **Stage 2 (Question Engine):** Candidate Resume + JD skill gap analysis, 15-question tree generation (`interview_questions.json`), and custom dynamic system prompt generation (`system_prompt.txt`).
3. **Stage 3 (Voice-to-Voice Loop):** Live AI voice interviewer (`Eva` persona in Ollama `qwen2.5:1.5b`), Silero VAD v3, Faster-Whisper STT, Kokoro-82M TTS, continuous raw PCM mic capture (`continuous_mic_input.wav`), and millisecond-accurate timing manifest (`session_manifest.json`).
4. **Stage 4 (Reports Engine):** Non-destructive turn audio slicer, 3-branch Gemini multimodal evaluator (Audio branch, Technical branch, Combine Synthesis branch), and final hiring report synthesis (`report.json` and `evaluation_summary.md`).

---

## 2. Architecture & Pipeline Handoff Chain

```
┌──────────────────────────────────────────────────────────────────────────┐
│  SetupScreen (Kivy UI)                                                   │
│  • Candidate Name & Seniority Selector                                   │
│  • Dual JD Input: Paste raw text  OR  Upload File (PDF/DOCX/TXT)         │
│  • Resume File Upload (PDF/DOCX/TXT)                                     │
│  • "🎯 Use Demo Data" button (Arjun Sharma + DataFlow Inc.)             │
└─────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Research Model (research_model/model/pipeline.py)              │
│  • SQLite Caching (`cache.db`) for instant re-runs (<1s)                │
│  • Output: InterviewRubric object (in-memory)                            │
└─────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Question Engine (question_model/model/question_generator.py)  │
│  • Gemini 3.6 Flash structured JSON schema generation                    │
│  • Output: interview_questions.json & system_prompt.txt                  │
└─────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────| File Name | Purpose & Functionality |
| --- | --- |
| `config.py` | Loads root `.env`, sets up session storage paths, and injects stage paths (`sys.path`) into Python module resolution cleanly. |
| `sample_data.py` | Built-in demo testing harness exposing `sample_resume.txt` and `sample_jd.txt` data. |
| `sample_resume.txt` | Pre-written candidate resume for Arjun Sharma (Senior Python Backend Engineer). |
| `sample_jd.txt` | Pre-written job description for DataFlow Inc. (Senior Backend Engineer). |
| `voice_engine.py` | Stage 3 loop controller that overrides Ollama's `SYSTEM_PROMPT` with Stage 2's dynamic prompt, handles the turn loop, manages `ContinuousMicWriter`, and logs turn timing data. |
| `orchestrator.py` | Master thread coordinator executing Stage 1 → Stage 2 → Stage 3 → Stage 4 in background threads with live progress callbacks to the UI. Accepts `max_questions` parameter (5 questions max fast testing vs 15 context live). |
| `front.py` | Main Kivy Desktop application implementing the 5-screen `ScreenManager` (`SetupScreen`, `ResearchScreen`, `QuestionScreen`, `InterviewScreen`, `ReportScreen`). |
| `test_pipeline.py` | Standalone CLI headless test runner executing Stage 1 → 2 → 3 → 4 end-to-end with 5-question test scoping. |
| `run.bat` | Batch launcher script for direct execution. |

---

## 4. 5-Phase Kivy Desktop GUI Screens

1. **`SetupScreen`**: Input screen for candidate metadata, Question Limit Selector (`Fast Testing (5 Questions)` vs `Real-Time Live (15 Questions)`), JD (paste or file upload), resume file upload, and demo data filling.
2. **`ResearchScreen`**: Live progress bar & scrollable log console displaying Stage 1 market research and rubric synthesis.
3. **`QuestionScreen`**: Displays generated question cards with topic and difficulty badges.
4. **`InterviewScreen`**: Live voice interview dashboard featuring active question display card, turn counter (`Turn X / Y`), live status indicator, scrollable candidate transcript box, and emergency stop button.
5. **`ReportScreen`**: Final evaluation report card displaying Overall Technical Score, Vocal Confidence Score, Hiring Signal badge, Executive Summary, Pillar breakdowns, and **Export Artifacts** button.

---

## 5. Session Output Artifact Lifecycle

All generated files from a single interview session are saved to a timestamped folder under `model/workflow/test/output/sess_<timestamp>/` (or active `sessions/sess_<timestamp>/`):

```
model/workflow/test/output/sess_20260726_145000/
├── interview_questions.json     ← Stage 2 Output
├── system_prompt.txt            ← Stage 2 Output
├── continuous_mic_input.wav     ← Stage 3 Output (raw 16kHz mono mic)
├── session_manifest.json        ← Stage 3 Output (turn millisecond telemetry)
├── turn_01.wav … turn_05.wav   ← Stage 4 Output (sliced turn clips)
├── report.json                  ← Stage 4 Output (structured JSON payload)
└── evaluation_summary.md        ← Stage 4 Output (Markdown report summary)
```

---

## 6. Execution & Verification

Run via root `backend/run.bat` menu:
- Select **Option 1: Launch Unified 5-Screen Netran AI Interview Workflow**
  - Mode 1: Kivy Desktop GUI Client (`front.py`)
  - Mode 2: Headless CLI Test Harness (`test_pipeline.py`)

Or run directly via Python CLI:
```bash
# Kivy Desktop GUI
python -m model.workflow.model.front

# Headless CLI Test Harness
python -m model.workflow.model.test_pipeline
```le upload), resume file upload, and demo data filling.
2. **`ResearchScreen`**: Live progress bar & scrollable log console displaying Stage 1 market research and rubric synthesis.
3. **`QuestionScreen`**: Displays generated 15-question cards with topic and difficulty badges.
4. **`InterviewScreen`**: Live voice interview dashboard featuring active question display card, turn counter (`Turn X / 15`), live status indicator, scrollable candidate transcript box, and emergency stop button.
5. **`ReportScreen`**: Final evaluation report card displaying Overall Technical Score, Vocal Confidence Score, Hiring Signal badge, Executive Summary, Pillar breakdowns, and **Export Artifacts** button.

---

## 5. Session Output Artifact Lifecycle

All generated files from a single interview session are saved to a timestamped folder under `model/workflow/test/output/sess_<timestamp>/` (or active `sessions/sess_<timestamp>/`):

```
model/workflow/test/output/sess_20260726_145000/
├── interview_questions.json     ← Stage 2 Output
├── system_prompt.txt            ← Stage 2 Output
├── continuous_mic_input.wav     ← Stage 3 Output (raw 16kHz mono mic)
├── session_manifest.json        ← Stage 3 Output (turn millisecond telemetry)
├── turn_01.wav … turn_05.wav   ← Stage 4 Output (sliced turn clips)
├── report.json                  ← Stage 4 Output (structured JSON payload)
└── evaluation_summary.md        ← Stage 4 Output (Markdown report summary)
```

---

## 6. Execution & Verification

Run via root `backend/run.bat` menu:
- Select **Option 1: Launch Unified 5-Screen Netran AI Interview Workflow**
  - Mode 1: Kivy Desktop GUI Client (`front.py`)
  - Mode 2: Headless CLI Test Harness (`test_pipeline.py`)

Or run directly via Python CLI:
```bash
# Kivy Desktop GUI Client
python -m model.workflow.model.front

# Headless CLI Test Harness
python -m model.workflow.model.test_pipeline
```
