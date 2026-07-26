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
| `config.py` | Configuration loader (`Stage2Config`) loading `GEMINI_API_KEY` and `GEMINI_MODEL` (`gemini-3.6-flash`). |
| `prompts.py` | Centralized system prompt repository containing `SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE`, `STAGE2_FULL_PROMPT_TEMPLATE`, and `FALLBACK_SYSTEM_PROMPT_TEMPLATE`. |
| `schemas.py` | Pydantic v2 schemas (`QuestionItem`, `Stage2Output`) enforcing strict JSON schema constraints. |
| `cache.py` | Class-based SQLite hashing subsystem (`Stage2Cache`) caching Stage 2 question trees by SHA-256 hash. |
| `pipeline.py` | Master Stage 2 orchestrator pipeline (`Stage2Pipeline`) executing resume parsing, cache check, Gemini prompt generation, and artifact saving. |
| `prompt_builder.py` | Class-based `PromptBuilder` constructing base instruction guardrails for Gemini system prompt synthesis. |
| `resume_parser.py` | Multimodal `ResumeParser` supporting `.pdf` (`pypdf`), `.docx` (`python-docx`), `.txt`, and `.json` files. |
| `question_generator.py` | Backward-compatibility alias wrapping `pipeline.py`. |
| `front.py` | Kivy Desktop GUI Client for Stage 2. |
| `test_pipeline.py` | Standalone CLI test suite that executes Stage 2 pipeline and verifies output artifacts. |

---

## 3. Data Flow & Output Artifacts

```
                       ┌────────────────────────┐
                       │ Stage 1: Market Rubric │
                       └───────────┬────────────┘
                                   │
┌─────────────────┐                ▼                ┌────────────────┐
│ Candidate Resume│ ───►  question_generator.py ───►│ Gemini 3.6     │
│ (PDF/DOCX/TXT/JSON) ───►  question_generator.py ───►│ Gemini 3.6     │
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

- **Output Session Directory: `test/output/sess_<timestamp>/`**
  - **`interview_questions.json`**: JSON array of 15 structured technical questions categorized into:
    - **Tier 1 (Warmup / Foundations):** Questions 1–2
    - **Tier 2 (Core Arch / Production):** Questions 3–12
    - **Tier 3 (Advanced / System Design):** Questions 13–15
    - Includes `id`, `topic`, `difficulty`, `question_text`, `expected_keywords`, and `resume_reference`.
  - **`interviewer_behavior.json`**: JSON object encapsulating:
    - `session_id`, `persona` ("Eva"), `target_seniority`, `interviewer_system_prompt`, and `behavior_rules` (1-2 sentence response limits for streaming voice execution).

---

## 4. Execution & Testing

- **Preset JSON Input Samples (`model/question_model/test/input/`):**
  - `sample_job_detail.json` & `sample_resume.json`
  - Subdirectories: `sample_backend/`, `sample_frontend/`
- **Output Session Folder Artifacts (`model/question_model/test/output/sess_<timestamp>/`):**
  - `interview_questions.json`
  - `interviewer_behavior.json`

Run via `run.bat` menu:
- Select **Option 3: Run Stage 2 Question Engine** (Choose 1 for Kivy GUI Desktop App, 2 for CLI Test Harness)

Or run directly via Python CLI:
```bash
# Launch Stage 2 Kivy Desktop GUI App
python -m model.question_model.model.app

# Run Headless CLI Test Harness
python -m model.question_model.model.test_pipeline
```
