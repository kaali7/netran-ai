# Stage 2: Adaptive Contextual & Behavioral Intelligence Engine - Technical Documentation

**Status:** ✅ **UPGRADED & OPERATIONAL**  
**Last Updated:** July 27, 2026  
**Module Location:** `backend/model/question_model/model/`  
**Doc Location:** `backend/model/question_model/doc/`  

---

## 1. Overview & Objective

The **Adaptive Contextual & Behavioral Intelligence Engine (Stage 2)** transforms raw Job Descriptions or Stage 1 Market Intelligence outputs (`stage1_output.json` / `sess_<timestamp>.json`) and Candidate Resumes (PDF/DOCX/TXT/JSON) into an adaptive, multi-artifact interview execution bundle:

1. **Resume Analysis & Skill Gap Matrix (`resume_analysis.json`):** Evaluates candidate proficiency tiers (`Foundational`, `Intermediate`, `Production Master`), identifies missing requirements from JD/Rubric, highlights warning flags, and selects top projects to probe.
2. **Branching Question Tree (`interview_questions.json`):** 15 stratified technical questions across 3 tiers with 3-level evaluation rubrics (`poor_answer_indicators`, `good_answer_indicators`, `bar_raiser_indicators`) and 2-way branching paths (`followup_if_strong`, `followup_if_weak`).
3. **Interviewer Behavior & System Prompt (`interviewer_behavior.json` & `system_prompt.txt`):** Generates Eva's persona configuration and latency-constrained voice system prompt (1–2 sentence max for Qwen2.5:3b in Stage 3).

---

## 2. File & Component Breakdown

| File Name | Purpose & Functionality |
| --- | --- |
| `config.py` | Configuration loader (`Stage2Config`) loading `GEMINI_API_KEY` and `GEMINI_MODEL` (`gemini-3.6-flash`). |
| `prompts.py` | Centralized system prompt repository containing `SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE`, `STAGE2_FULL_PROMPT_TEMPLATE`, and `FALLBACK_SYSTEM_PROMPT_TEMPLATE`. |
| `schemas.py` | Pydantic v2 schemas (`SkillMatch`, `SkillGap`, `ResumeAnalysis`, `AnswerRubric`, `QuestionItem`, `InterviewerBehavior`, `Stage2Output`). |
| `prompt_builder.py` | Class-based `Stage2PromptBuilder` with `extract_job_context` parsing nested Stage 1 outputs and legacy flat JDs. |
| `cache.py` | Class-based SQLite hashing subsystem (`Stage2Cache`) caching Stage 2 outputs by SHA-256 hash with schema validation error recovery. |
| `pipeline.py` | Master Stage 2 orchestrator pipeline (`Stage2Pipeline`) executing resume parsing, cache check, Gemini prompt generation, and 4-artifact saving. |
| `resume_parser.py` | Multimodal `ResumeParser` supporting `.pdf` (`pypdf`), `.docx` (`python-docx`), `.txt`, and `.json` files. |
| `question_generator.py` | Backward-compatibility alias wrapping `pipeline.py`. |
| `front.py` | Kivy Desktop GUI Client displaying Resume Analysis Matrix, Question Cards with Rubrics & Branching badges, System Prompt, and Session History Modal. |
| `test_pipeline.py` | Standalone CLI test harness supporting Stage 1 output ingestion, preset loading (`sample_backend`, `sample_frontend`, `sample_fullstack`), and artifact validation. |

---

## 3. Data Flow & Output Artifacts

```
                       ┌────────────────────────┐
                       │ Stage 1: Market Rubric │
                       └───────────┬────────────┘
                                   │
┌─────────────────┐                ▼                ┌────────────────┐
│ Candidate Resume│ ───►      pipeline.py     ───►│ Gemini 3.6     │
│ (PDF/DOCX/TXT)  │                                 └───────┬────────┘
└─────────────────┘                                         │
                                                            ▼
                                           ┌────────────────────────────────┐
                                            │  test/output/sess_<timestamp>/ │
                                            ├────────────────────────────────┤
                                            │ • resume_analysis.json         │
                                            │ • interview_questions.json     │
                                            │ • interviewer_behavior.json    │
                                            └────────────────────────────────┘
```

### Artifact Specifications

- **Output Session Directory: `model/question_model/test/output/sess_<timestamp>/`**
  1. **`resume_analysis.json`**:
     - `extracted_skill_overlap`: `skill`, `resume_evidence`, `proficiency_tier`.
     - `experience_gaps`: `missing_skill`, `jd_importance`, `probing_strategy`.
     - `project_relevance_scores`: `project_name`, `relevance_score`, `reasoning`.
     - `candidate_highlights`: Top candidate achievements, strengths, and green flags.
     - `resume_red_flags`: Warning signals or unverified claims.
  2. **`interview_questions.json`**: Array of 15 structured holistic questions categorized into:
     - **Personal & Behavioral Intro:** Questions 1–2 (Identity & culture/personality probe)
     - **Role Alignment & Fit:** Question 3
     - **Work Experience & History:** Questions 4–5
     - **Project Deep Dives:** Questions 6–8
     - **Core Technical Domain:** Questions 9–13
     - **System Design & Advanced Architecture:** Questions 14–15
     - Includes `rubric` (`poor_answer_indicators`, `good_answer_indicators`, `bar_raiser_indicators`), `followup_if_strong`, and `followup_if_weak`.
  3. **`interviewer_behavior.json`**:
     - `session_id`, `persona` ("Eva"), `target_company`, `candidate_name`, `target_role`, `interviewer_system_prompt`, `behavior_rules`.

---

## 4. Execution & Testing

- **Preset Input Subdirectories (`model/question_model/test/input/`):**
  - `sample_backend/`, `sample_frontend/`, `sample_fullstack/`
- **Output Session Folders (`model/question_model/test/output/sess_<timestamp>/`):**
  - Contains `resume_analysis.json`, `interview_questions.json`, `interviewer_behavior.json`, and `system_prompt.txt`.

Run via `run.bat` menu:
- Select **Option 3: Run Stage 2 Question Engine**

Or run directly via Python CLI:
```bash
# Launch Stage 2 Kivy Desktop GUI App
.\.venv\Scripts\python.exe -m model.question_model.model.front

# Run Headless CLI Test Harness
.\.venv\Scripts\python.exe -m model.question_model.model.test_pipeline
```
