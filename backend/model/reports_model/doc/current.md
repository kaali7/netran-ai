# Stage 4 — Multimodal Evaluation & Report Generation Engine (Current Status)

**Status:** ✅ **COVERED & OPERATIONAL**  
**Subsystem Directory:** `backend/model/reports_model/`  
**Last Updated:** July 26, 2026  

---

## 1. Subsystem Overview

Stage 4 is the post-session analytics and synthesis subsystem of Netran AI. It ingests:
- `continuous_mic_input.wav` / `recording.wav`: Raw continuous audio recording from Stage 3.
- `session_manifest.json` / `transcript.json`: Per-turn millisecond timing telemetry from Stage 3.

By leveraging **Gemini Multimodal Cloud API** (`gemini-3.6-flash` via the Interactions API), Stage 4 evaluates both candidate response accuracy (technical depth against Stage 1 rubrics) and vocal delivery dynamics (confidence, hesitation, emotion, filler word density).

---

## 2. Component Architecture & Test Harness Directory Layout

```
backend/model/reports_model/
├── doc/
│   ├── current.md              # Stage 4 technical implementation status
│   └── prd.md                  # Stage 4 Product Requirements Document
├── test/                       # Stage 4 standardized test harness directories
│   ├── input/                  # Stage 3 preset input sessions (sample_session/)
│   └── output/                 # Generated session report artifacts (sess_<timestamp>/)
└── model/
    ├── prompts.py              # Centralized system prompts (AUDIO_SYSTEM_PROMPT, TECHNICAL_SYSTEM_PROMPT, COMBINE_SYSTEM_PROMPT)
    ├── report_schema.py        # Pydantic v2 data models for report payload & evaluation outputs
    ├── audio_slicer.py         # Non-destructive WAV slicing utility
    ├── gemini_evaluator.py     # 3-stage Gemini multimodal evaluation engine (Audio, Technical, Combine)
    ├── report_builder.py       # Pipeline orchestrator & artifact renderer (JSON + Markdown)
    ├── test_pipeline.py        # CLI headless verification runner
    └── test_ui.py              # Interactive Kivy desktop testing application
```

---

## 3. Evaluation Flow & Pipeline

```
  continuous_mic_input.wav + session_manifest.json (from test/input/sample_session/)
                         │
                         ▼
             ┌──────────────────────┐
             │   audio_slicer.py    │
             └───────────┬──────────┘
                         │ Slices turn_XX.wav clips
                         ▼
        ┌──────────────────────────────────┐
        │       gemini_evaluator.py        │
        │ ┌──────────────┐ ┌─────────────┐ │
        │ │ Audio Branch │ │Tech Branch  │ │
        │ │ (Files API)  │ │(Rubric LLM) │ │
        │ └──────┬───────┘ └──────┬──────┘ │
        │        └───────┬────────┘        │
        │                ▼                 │
        │         Combine Branch           │
        └────────────────┬─────────────────┘
                         │ CandidateReportPayload
                         ▼
             ┌──────────────────────┐
             │  report_builder.py   │
             └───────────┬──────────┘
                         │ Writes artifacts
                         ▼
   backend/model/reports_model/test/output/sess_<timestamp>/
   ├── report.json
   └── evaluation_summary.md
```

---

## 4. Key Artifacts Produced

Inside `test/output/sess_<timestamp>/` (or active `backend/sessions/<session_id>/`):
1. `report.json`: Machine-readable Pydantic JSON payload for dashboard rendering and analytics storage.
2. `evaluation_summary.md`: Human-readable Markdown summary with scorecards, pillar breakdowns, and turn-by-turn audio notes.
3. `turn_XX.wav`: Per-turn sliced audio clips.

---

## 5. Running & Verification Commands

- **Kivy Desktop Test UI:**
  ```cmd
  python -m model.reports_model.model.test_ui
  ```

- **Headless CLI Test Pipeline:**
  ```cmd
  python -m model.reports_model.model.test_pipeline
  ```

- **Interactive System Launcher:**
  Run `run.bat` and select Option `3` (Kivy UI) or Option `4` (CLI).
