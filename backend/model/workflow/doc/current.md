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
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Voice Interview (workflow/model/voice_engine.py)              │
│  • Overrides Ollama brain persona with dynamic Stage 2 prompt            │
│  • Silero VAD + Faster-Whisper STT + Qwen2.5 LLM + Kokoro TTS           │
│  • Auto-stops after 15 questions                                         │
│  • Output: continuous_mic_input.wav & session_manifest.json              │
└─────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Reports Engine (reports_model/model/report_builder.py)        │
│  • WAV Slicing + Gemini Multimodal 3-Branch Evaluation                   │
│  • Output: report.json & evaluation_summary.md                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. File & Component Breakdown

| File Name | Purpose & Functionality |
| --- | --- |
| `config.py` | Loads root `.env`, sets up session storage paths, and injects stage paths (`sys.path`) into Python module resolution cleanly. |
| `sample_data.py` | Built-in demo testing harness exposing `sample_resume.txt` and `sample_jd.txt` data. |
| `sample_resume.txt` | Pre-written candidate resume for Arjun Sharma (Senior Python Backend Engineer). |
| `sample_jd.txt` | Pre-written job description for DataFlow Inc. (Senior Backend Engineer). |
| `voice_engine.py` | Stage 3 loop controller that overrides Ollama's `SYSTEM_PROMPT` with Stage 2's dynamic prompt, handles the 15-question loop, manages `ContinuousMicWriter`, and logs turn timing data. |
| `orchestrator.py` | Master thread coordinator executing Stage 1 → Stage 2 → Stage 3 → Stage 4 in background threads with live progress callbacks to the UI. |
| `app.py` | Main Kivy Desktop application implementing the 5-screen `ScreenManager` (`SetupScreen`, `ResearchScreen`, `QuestionScreen`, `InterviewScreen`, `ReportScreen`). |
| `requirements.txt` | Consolidated dependencies for the workflow module. |
| `run.bat` | Batch launcher script for direct execution. |

---

## 4. 5-Phase Kivy Desktop GUI Screens

1. **`SetupScreen`**: Input screen for candidate metadata, JD (paste or file upload), resume file upload, and demo data filling.
2. **`ResearchScreen`**: Live progress bar & scrollable log console displaying Stage 1 market research and rubric synthesis.
3. **`QuestionScreen`**: Displays generated 15-question cards with topic and difficulty badges.
4. **`InterviewScreen`**: Live voice interview dashboard featuring active question display card, turn counter (`Turn X / 15`), live status indicator, scrollable candidate transcript box, and emergency stop button.
5. **`ReportScreen`**: Final evaluation report card displaying Overall Technical Score, Vocal Confidence Score, Hiring Signal badge, Executive Summary, Pillar breakdowns, and **Export Artifacts** button.

---

## 5. Session Output Artifact Lifecycle

All generated files from a single interview session are saved to a timestamped folder under `backend/model/sessions/sess_<timestamp>/`:

```
backend/model/sessions/sess_20260725_134439/
├── interview_questions.json     ← Stage 2 Output
├── system_prompt.txt            ← Stage 2 Output
├── continuous_mic_input.wav     ← Stage 3 Output (raw 16kHz mono mic)
├── session_manifest.json        ← Stage 3 Output (turn millisecond telemetry)
├── turn_01.wav … turn_15.wav   ← Stage 4 Output (sliced turn clips)
├── report.json                  ← Stage 4 Output (structured JSON payload)
└── evaluation_summary.md        ← Stage 4 Output (Markdown report summary)
```

---

## 6. Execution & Verification

Run via root `backend/run.bat` menu:
- Select **Option 1: RUN COMPLETE UNIFIED NETRAN AI WORKFLOW (Stage 1 to 4 Kivy UI)**

Or run directly via Python CLI:
```bash
cd backend/model/workflow/model
python app.py
```
