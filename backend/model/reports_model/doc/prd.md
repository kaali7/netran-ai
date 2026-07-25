# Product Requirements Document (PRD)

## Project Name: Netran AI (SAMWINI) - Subsystem: Post-Session Multimodal Evaluation & Report Generation Engine (Stage 4)

**Document Type:** Technical & Functional Specifications for Multimodal Audio-Grounded Analytics & Report Synthesis

**Academic Year:** 2026-27

**Authors:** Samta Sakha & Ashwini Prajapati

---

## 1. Project Overview & Objective

The **Post-Session Multimodal Evaluation & Report Generation Engine (Stage 4)** is the final analytical subsystem of Netran AI. Following the conclusion of a voice-to-voice interview, this module ingests the raw, continuous audio recording (`continuous_mic_input.wav`) alongside millisecond-precision timing telemetry (`session_manifest.json`) generated in Stage 3.

By leveraging the **Gemini Cloud API's native multimodal audio capabilities**, Stage 4 evaluates both *what* the candidate said (technical transcript accuracy against Stage 1 rubrics) and *how* they said it (vocal confidence, tone stability, emotional state, and initial hesitation). The objective is to synthesize a structured, audio-grounded evaluation matrix that delivers actionable feedback for candidates and objective hiring signals for technical recruiters.

### 1.1 Problem Statement

Traditional interview evaluation engines suffer from critical blind spots:

* **Text-Only Disconnect:** Standard LLM evaluations evaluate raw text transcripts, completely missing vocal hesitation, nervousness, lack of confidence, or artificial long pauses.
* **Transcript Hallucination Risks:** Cascaded STT models often drop tech terminology or mistranscribe spoken syntax, leading downstream evaluation models to penalize candidates unfairly.
* **Unstructured Feedback:** Generic AI interview reports lack standardized scoring schemas, making it impossible to compare candidates objectively across core technical pillars.

---

## 2. Scope & Target Audience

### 2.1 Primary Users

* **Job Seekers & Candidates:** Receives targeted feedback breaking down technical knowledge gaps alongside vocal delivery advice (pacing, reducing filler words, building production confidence).
* **Engineering Hiring Managers & Recruiters:** Obtains an objective, rubric-grounded assessment featuring an executive hiring signal (*Strong Hire* to *No Hire*) and a competency matrix.
* **Netran AI Kivy Desktop GUI:** Consumes structured report artifacts (`report.json` and `evaluation_summary.md`) to render interactive performance dashboards in the desktop interface.

---

## 3. Core Features & Functional Requirements

### 3.1 Millisecond-Precision Audio Slicing

* **Manifest-Driven Extraction:** The system must parse `session_manifest.json` to extract start (`audio_start_sec`) and end (`audio_end_sec`) timestamps for every turn.
* **Asynchronous Clip Generation:** An internal utility (`audio_slicer.py`) will slice `continuous_mic_input.wav` into individual per-turn WAV files (`turn_01.wav`, `turn_02.wav`, etc.) inside `backend/sessions/<session_id>/` without blocking the UI thread.

### 3.2 Cloud-Native Multimodal Audio & Transcript Analysis

* **Direct Audio Byte Streaming:** Per-turn WAV clips will be passed directly as raw audio bytes to the Gemini Cloud API (`gemini-2.5-flash`), eliminating local GPU memory contention with Ollama and Whisper.
* **Audio-Grounded STT Verification:** Gemini will listen directly to the audio waveform to verify and refine transcript accuracy, correctly catching complex technical terms (e.g., "hydration", "closure", "virtual DOM") that fast local STT models might misinterpret.
* **Acoustic Emotion & Tone Evaluation:** Gemini will evaluate vocal tone, pitch stability, emotional state (e.g., *Calm*, *Stressed*, *Uncertain*), filler word density, and hesitation levels directly from the candidate's voice clip.

### 3.3 Fused Multi-Modal Synthesis Engine

* **Cross-Correlation Matrix:** The engine must fuse qualitative audio tone with quantitative transcript correctness. It will explicitly identify patterns such as:
* *High Technical Score + Low Vocal Confidence:* Indicates theoretical knowledge lacking production hands-on experience.
* *Low Technical Score + High Vocal Confidence:* Indicates fluent or overconfident delivery masking shallow knowledge.


* **Rubric Mapping:** Every turn evaluation must map directly back to the target technical pillars established in Stage 1's interview rubric.

### 3.4 Strict Pydantic Schema Output & Artifact Generation

* **Type-Safe Validation:** Report generation will enforce strict JSON structures using Pydantic models (`CandidateReportPayload`).
* **Dual-Perspective Artifacts:** The module must atomically generate two files inside `backend/sessions/<session_id>/`:
1. `report.json`: Machine-readable payload for GUI rendering, database archiving, and analytical export.
2. `evaluation_summary.md`: Formatted Markdown document for reading and immediate PDF export.



---

## 4. Technical Specifications & Architecture

```
  ┌──────────────────────────────────────────────────────────────┐
  │         backend/sessions/<session_id>/ Artifacts            │
  │         • continuous_mic_input.wav                           │
  │         • session_manifest.json                              │
  │         • Stage 1 Rubric / Track Requirements                │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 1. Turn Audio Extractor (audio_slicer.py)                    │
  │    • Slices continuous_mic_input.wav by manifest timestamps  │
  │    • Output: turn_01.wav, turn_02.wav, etc.                   │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 2. Multimodal Gemini Evaluator (gemini_evaluator.py)         │
  │    • Input: [turn_XX.wav] + [Question] + [Stage 1 Rubric]    │
  │    • Engine: google-genai SDK (gemini-2.5-flash)              │
  │    • Metrics: Tone, Hesitation, STT Grounding, Accuracy      │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 3. Pydantic Structured Synthesis (report_builder.py)         │
  │    • Schema: CandidateReportPayload                          │
  │    • Merges turn scores into overall technical & vocal score │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 4. Artifact Finalization                                     │
  │    • Writes report.json & evaluation_summary.md              │
  │    • Dispatches callback to Kivy Desktop GUI                 │
  └──────────────────────────────────────────────────────────────┘

```

### 4.1 Backend Pipeline Stack

* **Language & Audio Processing:** Python 3.11 with standard `wave` library for fast, lightweight audio waveform trimming (`audio_slicer.py`).
* **Schema Validation & Enforcement:** **Pydantic v2** models (`report_schema.py`) enforcing integer boundaries ($1{-}10$ turn ratings, $0{-}100$ pillar scores) and string-based enums.
* **Multimodal Engine:** Official `google-genai` Python SDK (`from google import genai`) configured with `gemini-3.6-flash` and structured schema parsing.
* **API Key Management:** System reads `GEMINI_API_KEY` securely from `.env`.

### 4.2 Data Layer & Schema Constraints

The generated `CandidateReportPayload` must strictly satisfy the following contract:

| Object / Field | Type | Description |
| --- | --- | --- |
| `session_id` | `str` | Unique session identifier (e.g., `sess_20260724_201422`). |
| `overall_hiring_signal` | `str` Enum | `"Strong Hire"`, `"Hire"`, `"Lean No Hire"`, `"No Hire"`. |
| `overall_technical_score` | `int` ($0{-}100$) | Aggregated score across technical domain questions. |
| `overall_vocal_confidence_score` | `int` ($0{-}100$) | Aggregated score evaluating vocal delivery, tone, and pacing. |
| `technical_pillars` | `List[PillarScore]` | Domain-specific breakdowns (e.g., *React Internals*, *System Architecture*). |
| `turn_evaluations` | `List[TurnAnalysis]` | Per-turn breakdowns containing `transcript`, `technical_score`, `confidence_score`, `hesitation_level`, `emotional_state`, and `missing_concepts`. |

---

## 5. Development Timeline (Mapped to Main 8-Week Sprint)

* **Week 5 (Early):** Implement `audio_slicer.py` and test audio clipping against Stage 3 continuous WAV files and session manifests.
* **Week 5 (Late):** Set up `gemini_evaluator.py` using `google-genai` SDK and construct prompt wrappers for multimodal audio byte streaming.
* **Week 6 (Early):** Define Pydantic schema structures in `report_schema.py` and implement synthesis routines in `report_builder.py`.
* **Week 6 (Late):** Implement error handling for network timeouts or corrupted audio clips, adding retry logic for Gemini Cloud API calls.
* **Week 7:** Wire the background Stage 4 execution trigger to the **Stop Interview** action in the Kivy Desktop application.
* **Week 8:** End-to-end integration testing (verifying that stopping an interview generates valid `report.json` and `evaluation_summary.md` artifacts and renders them cleanly in the UI).

---

## 6. Future Scope

* **Visual Pitch & Energy Charts:** Extending the Kivy UI to render continuous waveform graphs alongside Gemini's turn-by-turn confidence markers.
* **Historical Progress Tracking:** Storing evaluation reports in PostgreSQL to allow candidates to track technical growth and vocal confidence improvements across multiple interview sessions over time.