# Stage 2: Contextual Question & Behavioral Prompt Engine - Technical Documentation

**Status:** ✅ **COVERED & OPERATIONAL**  
**Module Location:** `backend/model/question_model/model/`  
**Doc Location:** `backend/model/question_model/doc/`  

---

## 1. Overview & Objective

The **Contextual Question & Behavioral Prompt Engine (Stage 2)** sits between **Stage 1 (JD Research & Market Intel)** and **Stage 3 (Live Streaming Voice-to-Voice Loop)**.

By analyzing the Candidate's Resume (PDF/DOCX/TXT) alongside the target Job Description (JD) and Stage 1 Rubric, Stage 2 performs:
1. **Skill Cross-Matching & Gap Analysis:** Identifies strong overlaps (for deep technical probing) and missing skills (for foundational verification).
2. **Dynamic Question Tree Generation (`interview_questions.json`):** Constructs 15 ordered technical questions stratified across 3 difficulty tiers (Junior, Mid, Senior) tailored to the candidate's resume projects and JD pillars.
3. **Custom Behavioral System Prompt Construction (`system_prompt.txt`):** Generates a latency-calibrated system prompt for Stage 3's `brain.py` (`Eva` persona in Ollama `qwen2.5:1.5b`), enforcing strict 1–2 sentence output constraints, probing strategies, and roleplay tone.

---

## 2. File & Component Breakdown

| File Name | Purpose & Functionality |
| --- | --- |
| `config.py` | Loads `GEMINI_API_KEY` and `GEMINI_MODEL` (`gemini-3.6-flash`) from root `.env`. |
| `schemas.py` | Pydantic v2 schemas (`QuestionItem`, `Stage2Output`) enforcing strict JSON schema constraints. |
| `resume_parser.py` | Multimodal resume extractor supporting `.pdf` (`pypdf`), `.docx` (`python-docx`), and `.txt` files. |
| `prompt_builder.py` | Constructs base instruction guardrails for Gemini to synthesize Stage 3 latency-constrained behavioral system prompts. |
| `question_generator.py` | Core reasoning engine using `google-genai` SDK (`gemini-3.6-flash`) with structured JSON schema output (`response_schema=Stage2Output`). Exports artifacts directly to session directories. |
| `test_pipeline.py` | Standalone CLI test suite that generates a mock candidate resume, executes the full Stage 2 pipeline, and verifies output artifacts. |

---

## 3. Data Flow & Output Artifacts

```
                       ┌────────────────────────┐
                       │ Stage 1: Market Rubric │
                       └───────────┬────────────┘
                                   │
┌─────────────────┐                ▼                ┌────────────────┐
│ Candidate Resume│ ───►  question_generator.py ───►│ Gemini 3.6     │
│ (PDF/DOCX/TXT)  │       (google-genai SDK)        │ Flash Engine   │
└─────────────────┘                                 └───────┬────────┘
                                                            │
                                                            ▼
                                           ┌────────────────────────────────┐
                                           │   backend/sessions/<sess_id>/   │
                                           ├────────────────────────────────┤
                                           │ • interview_questions.json     │
                                           │ • system_prompt.txt            │
                                           └────────────────────────────────┘
```

### Artifact Specifications

- **Single Consolidated Output File: `test/output/sess_<timestamp>.json`**
  - Encapsulates `session_id`, `interviewer_system_prompt` (Eva persona runtime system prompt), and `question_tree` (15 structured technical questions).
  - 15 questions categorized into:
    - **Tier 1 (Warmup / Foundations):** Questions 1–2
    - **Tier 2 (Core Arch / Production):** Questions 3–12
    - **Tier 3 (Advanced / System Design):** Questions 13–15
  - Each question includes `topic`, `difficulty`, `question_text`, `expected_keywords`, and `resume_reference`.

---

## 4. Execution & Testing

- **Preset JSON Input Samples:** `model/question_model/test/input/` (`sample_stage2_backend.json`, `sample_stage2_frontend.json`, `sample_stage2_fullstack.json`).
- **Single JSON Session Outputs:** `model/question_model/test/output/sess_<timestamp>.json`.

Run via `run.bat` menu:
- Select **Option 3: Run Stage 2 Question Engine (Headless CLI)**

Or run directly via Python CLI:
```bash
python -m model.question_model.model.test_pipeline
```
