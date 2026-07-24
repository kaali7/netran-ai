# Product Requirements Document (PRD)
## Project Name: Netran AI (SAMWINI)
**Document Type:** Technical & Functional Specifications for AI Voice-Based Mock Interview System  
**Academic Year:** 2026-27  
**Authors:** Samta Sakha & Ashwini Prajapati  

---

## 1. Project Overview & Objective
Netran AI is an intelligent, AI-powered virtual interviewer designed to simulate real-world job interview experiences through dynamic voice-based interactions. The system bridges the gap between theoretical preparation and practical execution by leveraging Large Language Models (LLMs), Speech-to-Text (STT), and Text-to-Speech (TTS) technologies to actively listen, adapt lines of questioning, and deliver data-driven feedback. 

### 1.1 Problem Statement
Candidates frequently struggle with real-world interview performance due to:
* Limited access to experienced interviewers and realistic practice environments.
* Generic preparation resources that lack personalized feedback.
* Difficulty identifying and addressing specific communication or behavioral weaknesses.

---

## 2. Scope & Target Audience
### 2.1 Primary Users
* **Students & Job Seekers:** Individuals preparing for campus placements or transitioning careers requiring practice against highly specific job descriptions.
* **Academic Institutions:** College placement cells utilizing the tool for round-the-clock student interview practice.
* **Corporate HR (Initial Screening):** Organizations using the system to conduct automated first-round voice interviews to evaluate baseline technical and communication skills.

---

## 3. Core Features & Functional Requirements

### 3.1 Student Module
* **Authentication:** Secure user registration and login.
* **Document Parsing:** Ability to upload resumes and Job Descriptions (JD) in PDF, DOCX, or plain text formats.
* **Interview Configuration:** 
  * Select specific domains (e.g., Software Development, Data Science, AI, DevOps, Cybersecurity).
  * Choose difficulty tiers (Beginner, Intermediate, Advanced).
* **Analytics Dashboard:** Visual performance tracking allowing users to review previous attempts and monitor improvement.

### 3.2 AI Interview Process Flow
1. **Data Extraction:** The backend NLP parses the uploaded JD and resume to extract key technical skills and domain expectations.
2. **Question Generation:** An LLM utilizes a strict prompt structure to generate context-aware questions tailored to the specified difficulty level.
3. **Voice Interaction Loop:**
   * **TTS:** Converts the AI's generated text into spoken audio for the user.
   * **STT:** Captures and transcribes the user's verbal response.
   * **Adaptive Reasoning:** The LLM evaluates the transcription for accuracy and confidence, dynamically generating the next appropriate follow-up question.
4. **Evaluation:** The system aggregates response data to score the candidate against the initial JD metrics, producing a comprehensive feedback report.

---

## 4. Technical Specifications & Architecture

### 4.1 Frontend Stack & UI/UX Guidelines
* **Frameworks:** React.js, Next.js, and TypeScript.
* **Styling:** Tailwind CSS. 
* **Design System:** The dashboard will feature a highly responsive, fast, and minimalist visual aesthetic. To align with a "serious tech" professional interface, the UI will implement a strict 60-30-10 color hierarchy utilizing black as the dominant background, white for core structural elements and typography, and deep purple for primary action buttons and data accents.

### 4.2 Backend & Data Layer
* **API Routing:** Python with FastAPI for handling rapid asynchronous requests between the user interface and AI models.
* **Database:** PostgreSQL for storing user profiles, historical text transcripts, and generated performance metrics.

### 4.3 AI & Machine Learning Infrastructure
* **Reasoning Engines:** Groq and Gemini APIs.
* **Audio Processing:** Integrated real-time STT and TTS services for voice synthesis and transcription.

### 4.4 Hardware Requirements
* **Development:** Multi-core processor (Intel i5/Ryzen 5+) with 8GB–16GB RAM.
* **End-User:** Any standard device with a modern web browser, microphone, and stable internet connection.

---

## 5. Development Timeline (8-Week Sprint)
The project will be executed in parallel tracks to ensure rapid deployment within a 2-month window:

* **Week 1:** Requirements & Planning.
* **Weeks 1-2:** UI/UX Design and Frontend Development.
* **Weeks 2-3:** Backend and PostgreSQL Database Setup.
* **Weeks 3-5:** AI API & NLP Pipeline Integration.
* **Weeks 4-5:** STT & TTS Voice System configuration.
* **Week 6:** Full System Integration.
* **Week 7:** Testing & Bug Fixing.
* **Week 8:** Final Documentation & Submission.

---

## 6. Future Scope
* **Multimodal Analysis:** Integrating video feeds to evaluate facial expressions and body language.
* **Localization:** Expanding support for multiple regional and international languages.
* **Platform Integrations:** Connecting directly to job portals like LinkedIn or Indeed for seamless one-click interview generation.
* **Recruiter Extension:** Developing a dedicated "Recruiter Dashboard" to manage automated candidate screening pipelines and review AI-generated applicant reports.

---

## 7. Stage 3 Enhancements — Continuous Recording & Session Manifest (Plan B)

### 7.1 Overview & Artifact Flow
To support downstream post-session candidate evaluations (Stage 4), Stage 3 records an uncompressed continuous microphone audio stream and outputs a millisecond-precision JSON transcript manifest upon interview completion.

```
                     ┌──────────────────────────────────────────────┐
                     │            STAGE 3 (Voice Loop)              │
                     └──────────────────────┬───────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
       [ continuous_mic_input.wav ]                  [ session_manifest.json ]
       (Full 16kHz PCM mic stream)                   (Live transcript + millisecond 
                                                      timestamps per turn)
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            │ Session Completed
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │            Shared Artifact Storage           │
                     │          (backend/sessions/<session_id>)     │
                     └──────────────────────┬───────────────────────┘
                                            │ (Future Stage 4)
                                            ▼
                                model/reports_model/model/
```

### 7.2 Session Artifact Specifications
Upon session completion, two artifacts are written to `backend/sessions/<session_id>/`:

#### 1. `continuous_mic_input.wav`
* **Format:** Uncompressed WAV (16kHz, 16-bit Mono PCM).
* **Worker:** `ContinuousMicWriter` background thread consuming audio queue asynchronously without blocking Silero VAD or Faster-Whisper loops.
* **Isolation:** Captures candidate microphone stream only (zero AI audio bleed).

#### 2. `session_manifest.json`
* **Format:** JSON structure linking transcripts directly with exact timing offsets.
* **Schema:**
```json
{
  "session_id": "sess_20260724_185500",
  "session_start_iso": "2026-07-24T18:55:00Z",
  "total_turns": 15,
  "turns": [
    {
      "turn_id": 1,
      "topic": "React State Management",
      "question_text": "How do you handle state persistence across route transitions in Next.js?",
      "candidate_transcript": "I usually use Zustand combined with local storage sync...",
      "audio_start_sec": 14.250,
      "audio_end_sec": 48.800,
      "silence_duration_before_answer_sec": 1.400,
      "stt_latency_ms": 320,
      "ttft_ms": 410
    }
  ]
}
```

### 7.3 Operational Safety & Edge-Case Protection
* **Abrupt Exit Handling:** `ContinuousMicWriter` uses `atexit` handlers and thread cleanup to ensure WAV headers are properly closed and formatted even during forced application exit.
* **Monotonic Timestamps:** All offset timestamps are calculated using `time.perf_counter()` to guarantee immunity against system clock drift or network time sync shifts.