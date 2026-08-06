# Stage 4 — Multimodal Evaluation & Report Generation Engine (Current Status)

**Status:** ✅ **COVERED & OPERATIONAL**  
**Subsystem Directory:** `backend/model/reports_model/`  
**Last Updated:** August 01, 2026  

---

## 1. Subsystem Overview

Stage 4 is the post-session analytics and synthesis subsystem of Netran AI. It ingests:
- `continuous_mic_input.wav` / `recording.wav`: Raw continuous audio recording from Stage 3.
- `session_manifest.json` / `transcript.json`: Per-turn millisecond timing telemetry from Stage 3.
- `sample_resume.txt` / `sample_resume.json`: Candidate resume context (Stage 1/2 Grounding).
- `sample_rubric.json` / `sample_job_detail.json`: Job rubric and pillar requirements (Stage 1 Grounding).

By leveraging **Gemini Multimodal Cloud API** (`gemini-3.6-flash` via the Interactions API), Stage 4 evaluates both candidate response accuracy (technical depth against Stage 1 rubrics + Resume claims) and vocal delivery dynamics (confidence, hesitation, emotion, filler word density). A 4-second anti-rate-limit pacing mechanism ensures stable execution within the Gemini Free Tier constraints.

---

## 2. Component Architecture & Test Harness Directory Layout

```
backend/model/reports_model/
├── doc/
│   ├── current.md              # Stage 4 technical implementation status
│   └── prd.md                  # Stage 4 Product Requirements Document
├── test/                       # Stage 4 standardized test harness directories
│   ├── input/                  # Stage 3 preset input sessions (sample1/, sample2/)
│   └── output/                 # Generated session report artifacts (sess_<timestamp>/)
└── model/
    ├── prompts.py              # Centralized dynamic system prompts with context injection functions
    ├── schemas.py              # Pydantic v2 models for report payload & evaluation outputs
    ├── audio_slicer.py         # Non-destructive WAV slicing utility
    ├── gemini_evaluator.py     # 3-stage Gemini multimodal evaluation engine (Audio, Technical, Combine)
    ├── pipeline.py             # Pipeline orchestrator & artifact renderer (JSON + Markdown) with Rate Limiting
    ├── test_pipeline.py        # CLI headless verification runner with dynamic interactive menu
    └── front.py                # Interactive Kivy desktop UI for testing
```

---

## 3. Evaluation Flow & Pipeline

```
  continuous_mic_input.wav + session_manifest.json + Context Files (Resume/Rubric)
                          │
                          ▼
              ┌──────────────────────┐
              │   audio_slicer.py    │
              └───────────┬──────────┘
                          │ Slices turn_XX.wav clips
                          ▼
         ┌──────────────────────────────────┐
         │       pipeline.py (Rate Limit)   │
         │                ▼                 │
         │       gemini_evaluator.py        │
         │ ┌──────────────┐ ┌─────────────┐ │
         │ │ Audio Branch │ │Tech Branch  │ │
         │ │ (Files API)  │ │(Rubric LLM) │ │
         │ └──────┬───────┘ └──────┬──────┘ │
         │        └───────┬────────┘        │
         │                ▼                 │
         │         Combine Branch           │
         │  (Progressive Cache Saving to    │
         │         turn_cache.json)         │
         └────────────────┬─────────────────┘
                          │ CandidateReportPayload
                          ▼
              ┌──────────────────────┐
              │  pipeline.py         │
              └───────────┬──────────┘
                          │ Writes artifacts
                          ▼
    backend/model/reports_model/test/output/sess_<timestamp>/
    ├── report.json
    └── evaluation_summary.md
```

---

## 4. Key Artifacts & Enhanced Executive Payload

Inside `test/output/sess_<timestamp>/` (or active `backend/sessions/<session_id>/`):
1. `report.json`: Machine-readable Pydantic JSON payload for dashboard rendering and analytics storage. Features:
   - **Precision Telemetry (`TurnTelemetry`):** Deterministic latency ms, clip duration sec, and STT Whisper hallucination detection flags.
   - **Behavioral Red Flags (`BehavioralFlag`):** Top-level array capturing critical events (e.g., session abort requests, severe acoustic-STT discrepancies).
   - **Candidate Upskilling Roadmap (`CandidateFeedback`):** Key strengths, primary growth areas, and recommended study topics.
   - **Context Fallback Grounding:** Automatic fallback notice when candidate resume or Stage 1 rubric is omitted.
2. `evaluation_summary.md`: Human-readable Markdown summary with scorecards, pillar breakdowns, integrity alerts, growth roadmaps, and turn-by-turn telemetry notes.
3. `turn_cache.json`: Progressively saved cache of `AudioBranchOutput` and `TechnicalBranchOutput` models. Enables instantaneous resume on failure and live GUI streaming during generation.
4. `turn_XX.wav`: Per-turn sliced audio clips.

---

## 5. Running & Verification Commands

- **Kivy Desktop Test UI:**
  ```cmd
  python -m model.reports_model.model.front
  ```

- **Headless CLI Test Pipeline (Interactive Session Picker):**
  ```cmd
  python -m model.reports_model.model.test_pipeline
  ```

- **Interactive System Launcher:**
  Run `run.bat` at the backend root and select Option `5` (Stage 4), then pick mode `1` (Kivy) or `2` (CLI).
