# Product Requirements Document (PRD)

## Project Name: Netran AI - Subsystem: Contextual Question & Behavioral Prompt Engine (Stage 2)

**Document Type:** Technical & Functional Specifications for Dynamic Question Tree & System Prompt Synthesis

**Academic Year:** 2026-27

**Authors:** Samta Sakha & Ashwini Prajapati

---

## 1. Project Overview & Objective

The **Contextual Question & Behavioral Prompt Engine (Stage 2)** bridges Stage 1 (Research & Market Rubric) and Stage 3 (Live Voice-to-Voice Loop). By synthesizing the structured market rubric from Stage 1 alongside the candidate's parsed Resume and target Job Description (JD), Stage 2 performs skill cross-matching, gap identification, and difficulty tiering.

Stage 2 generates **two core outputs**:

1. A structured **Question Tree (`interview_questions.json`)** tailored to the candidate's unique resume projects and technical background.
2. A customized **Interviewer Behavioral System Prompt** fed directly into Stage 3's live streaming voice LLM (`qwen2.5:3b` in `brain.py`), governing how the interviewer probes, handles shallow answers, and enforces latency-friendly concise responses.

### 1.1 Problem Statement

AI voice interviews frequently fail due to:

* **Generic, One-Size-Fits-All Question Sets:** Default AI interviewers ask textbook questions without probing candidate-specific resume claims or past engineering projects.
* **Lack of Persona Discipline in Voice Loops:** Without a contextually calibrated system prompt, the voice LLM in Stage 3 tends to output long multi-sentence explanations, breaking real-time latency targets (<1200ms TTFA) and disengaging the candidate.
* **Unstructured Question Progression:** Without pre-computed difficulty tiering (Junior, Mid, Senior), voice interviews lack a natural structural flow (e.g., jumping from basic syntax to complex architecture without warmup).

---

## 2. Scope & Target Audience

### 2.1 Primary Users

* **Job Seekers & Candidates:** Receives a personalized, realistic technical interview experience that directly references their past resume projects and tests their actual claims against JD expectations.
* **Stage 3 Voice Loop Subsystem (`voice_to_voice_model`):** Ingests the dynamic runtime system prompt and ordered question list to drive `brain.py` and enforce low-latency streaming interactions.

---

## 3. Core Features & Functional Requirements

### 3.1 Resume Parsing & Skill Cross-Matching Engine

* **Resume Ingestion:** The subsystem must extract structured text from candidate uploaded resumes (`.pdf`, `.docx`, `.txt`) using `resume_parser.py`.
* **Skill Overlap & Gap Matrix:** Compares Stage 1's key technical pillars against extracted resume skills:
* **Strong Overlap:** Generates high-difficulty production/debugging questions.
* **Missing / Unlisted Skills:** Generates foundational concept verification questions to detect technical blindspots.


* **Project Probing:** Extracts specific projects, frameworks, and architecture decisions from the resume to generate real-world probing questions (e.g., *"In your project Notara, how did you handle state hydration?"*).

### 3.2 Dynamic Question Tree Generation

* **Difficulty Tiering & Taxonomy:** Maps questions across three distinct tiers:
* *Tier 1: Warmup & Foundational Concepts* (1–2 questions)
* *Tier 2: Core Architecture & Hands-on Production* (8–10 questions)
* *Tier 3: Advanced Edge Cases & System Design* (3–4 questions)


* **Structured Output Enforcement:** Generates a strict JSON question list (`interview_questions.json`) satisfying exact Pydantic schema validation.

### 3.3 Dynamic Behavioral System Prompt Construction

* **Customized Persona Injection:** Generates the runtime system prompt for Stage 3's `brain.py` (`Eva` persona).
* **Guiding Rules & Guardrails:** Injects operational instructions:
* *Max Output Length:* Strict 1–2 sentence constraint to keep TTS execution fast.
* *Probing Strategy:* Instructs the LLM on when to push deeper if a candidate gives a vague answer versus moving to the next topic.
* *Tone & Seniority:* Adjusts interviewer strictness based on target candidate seniority level.



---

## 4. Technical Specifications & Architecture

```
  ┌──────────────────────────────────────────────────────────────┐
  │                        STAGE 2 INPUTS                        │
  │   • Stage 1 Output : JD Market Rubric & Key Pillars          │
  │   • User Input     : Parsed Resume (Skills, Projects)        │
  │   • Base System    : Question Generation Guardrails          │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 1. Resume Parser & Cross-Matcher (resume_parser.py)          │
  │    • Extracts PDF/DOCX text & isolates project experience    │
  │    • Computes Skill Gap & Overlap Matrix against JD Rubric   │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 2. Question Generator & Prompt Builder (question_generator.py)│
  │    • Engine: google-genai SDK (gemini-3.6-flash)              │
  │    • Enforces Pydantic Schema Output                         │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
  ┌──────────────────────────────┴───────────────────────────────┐
  │                     STAGE 2 DUAL OUTPUT                      │
  │                                                              │
  │   ┌──────────────────────────────────────────────────────┐   │
  │   │ OUTPUT 1: Question Tree (interview_questions.json)   │   │
  │   │ • 15 Tiered Technical Questions                      │   │
  │   │ • Resume Probing Anchors & Expected Keywords         │   │
  │   └──────────────────────────────────────────────────────┘   │
  │   ┌──────────────────────────────────────────────────────┐   │
  │   │ OUTPUT 2: Stage 3 Behavioral System Prompt           │   │
  │   │ • Tailored Runtime Persona for brain.py (qwen2.5:3b) │   │
  │   │ • Probing & Latency Guardrail Rules                  │   │
  │   └──────────────────────────────────────────────────────┘   │
  └──────────────────────────────────────────────────────────────┘

```

### 4.1 Backend Pipeline Stack

* **Language & Document Processing:** Python 3.11 with `pypdf` and `python-docx` for structured resume parsing (`resume_parser.py`).
* **Data Validation & Enums:** **Pydantic v2** (`schemas.py`) enforcing schema constraints on question lists, difficulty tiers, and prompt parameters.
* **Reasoning Engine:** `google-genai` SDK (`from google import genai`, model: `gemini-3.6-flash`) with structured JSON schema outputs (`response_mime_type="application/json"`).
* **Stage 3 Interface:** Writes generated artifacts directly into the session folder for immediate loading by `brain.py`.

### 4.2 Data Layer & Schema Constraints

The generated `Stage2Output` must strictly satisfy the following contract:

| Object / Field | Type | Description |
| --- | --- | --- |
| `session_id` | `str` | Unique session identifier (e.g., `sess_20260724_201422`). |
| `interviewer_system_prompt` | `str` | Formatted runtime system prompt injected into Ollama Qwen2.5:3b (`brain.py`). |
| `question_tree` | `List[QuestionItem]` | Ordered array of 15 structured technical questions. |
| `QuestionItem.id` | `int` | Sequential question index ($1{-}15$). |
| `QuestionItem.topic` | `str` | Technical domain pillar (e.g., *React Internals*, *Tailwind CSS*). |
| `QuestionItem.difficulty` | `str` Enum | `"Junior"`, `"Mid"`, `"Senior"`. |
| `QuestionItem.question_text` | `str` | Phrased technical interview question. |
| `QuestionItem.expected_keywords` | `List[str]` | Core architectural concepts expected in the candidate's response. |
| `QuestionItem.resume_reference` | `Optional[str]` | Referenced past project or skill from candidate resume. |

---

## 5. Development Timeline (Mapped to Main 8-Week Sprint)

* **Week 4 (Early):** Build `resume_parser.py` supporting PDF/DOCX text extraction and candidate project/skill isolation.
* **Week 4 (Late):** Implement `question_generator.py` using `google-genai` SDK to synthesize Stage 1 Rubric + Resume into `interview_questions.json`.
* **Week 5 (Early):** Implement `prompt_builder.py` to compile the dynamic, latency-optimized system prompt for Stage 3 `brain.py`.
* **Week 5 (Late):** Integrate Pydantic schema validation (`schemas.py`) and wire output generation directly to `backend/sessions/<session_id>/`.
* **Week 7:** End-to-end integration testing (verifying that uploading a resume and JD correctly generates both the dynamic prompt and question tree, initializing the Stage 3 voice loop smoothly).

---

## 6. Future Scope

* **Adaptive Mid-Interview Re-treeing:** Allowing Stage 3 VAD/STT telemetry to trigger Stage 2 in real-time to adjust remaining question difficulty up or down based on candidate performance.
* **Company Culture Tone Alignment:** Customizing the behavioral prompt tone (e.g., highly encouraging startup vibe vs. rigorous enterprise panel style).