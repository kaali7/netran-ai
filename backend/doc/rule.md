# Netran AI — Mandatory Project Rules & Agent Directives

> **IMPORTANT FOR ALL DEVELOPERS AND AI ASSISTANTS**:
> Read this document completely BEFORE making any code or configuration edits in this repository. All code contributions, refactoring, and feature additions must adhere strictly to these rules.

---

## 📌 Rule 1: Read Documentation Before Code Edits
Before modifying any source code in a model stage:
1. Inspect `model/<stage_folder>/doc/current.md` to understand current architecture and status.
2. Inspect `model/<stage_folder>/doc/prd.md` for feature requirements.
3. Inspect `doc/folder_strucuture.md` and `doc/tech_stack.md` for directory layout and framework conventions.

---

## 📌 Rule 2: Stage 1 (Research Model) I/O Contract
* **Input**: JSON file (`sample_jd_*.json`) or raw JD text / URL.
* **Output**: Single consolidated JSON file saved directly to:
  `model/research_model/test/output/sess_<timestamp>.json`
* **Trusted Web Domains**: Categorized across Technical (LeetCode, GitHub, StackOverflow, GeeksforGeeks, Blind `teamblind.com`, CareerCup `careercup.com`, Exponent `tryexponent.com`, ByteByteGo `bytebytego.com`, Educative `educative.io`), Market & Compensation (Levels.fyi `levels.fyi`, AmbitionBox `ambitionbox.com`, Wellfound `wellfound.com`, Glassdoor, LinkedIn, Reddit), and HR Screening (Workable `resources.workable.com`, LinkedIn, Glassdoor).


---

## 📌 Rule 3: Stage 2 (Question Model) Dual I/O Contract
* **Inputs**: Must consist of **TWO separate JSON files** per preset in `model/question_model/test/input/`:
  - `sample_job_detail.json` (Company, Role, Target Seniority, Tech Stack, JD text)
  - `sample_resume.json` (Candidate Name, Target Role, Experience Years, Skills, Resume text)
* **Outputs**: Must output a dedicated session directory `model/question_model/test/output/sess_<timestamp>/` containing **THREE session artifacts**:
  1. `resume_analysis.json`: Candidate skill overlap, experience gaps, project relevance scores, candidate highlights, and resume red flags.
  2. `interview_questions.json`: Array of 15 holistic interview questions (`id`, `tier`, `topic`, `difficulty`, `question_text`, `expected_keywords`, `rubric`, `followup_if_strong`, `followup_if_weak`) covering behavioral intro, role fit, work history, project deep dives, technical domain, and system design.
  3. `interviewer_behavior.json`: Object containing `session_id`, `persona` ("Eva"), `target_company`, `candidate_name`, `target_role`, `interviewer_system_prompt`, and low-latency voice streaming `behavior_rules`.

---

## 📌 Rule 4: Stage 3 (Voice-to-Voice Model) I/O Contract
* **Inputs**: Loaded from `model/voice_to_voice_model/test/input/`:
  - `interview_questions.json` (Question tree from Stage 2)
  - `interviewer_behavior.json` (Eva interviewer persona & system prompt from Stage 2)
* **Outputs**: Dedicated session directory `model/voice_to_voice_model/test/output/sess_<timestamp>/` containing:
  1. `recording.wav`: Continuous raw PCM/WAV candidate & interviewer mic audio.
  2. `transcript.json` / `session_manifest.json`: Turn-by-turn dialogue transcript with timestamp & latency telemetry (`stt_ms`, `llm_ms`, `tts_ms`).
* **Question Limit Scoping**:
  - **Testing Time**: Bounded to **5 questions max** (`MAX_QUESTIONS = 5`) for fast automated test harness execution.
  - **Real-Time Live Interview Time**: Supports **10 to 15 questions** (`MAX_QUESTIONS = 10..15`) tailored to job description requirements.

---

## 📌 Rule 5: Stage 4 (Reports Model) Dual I/O Contract
* **Inputs**: Loaded from `model/reports_model/test/input/sample_session/` or active session directory:
  - `continuous_mic_input.wav` / `recording.wav` (Continuous audio recording from Stage 3)
  - `session_manifest.json` / `transcript.json` (Per-turn millisecond timing telemetry from Stage 3)
* **Outputs**: Dedicated session directory `model/reports_model/test/output/sess_<timestamp>/` containing:
  1. `report.json`: Machine-readable Pydantic JSON report payload containing technical scores & vocal confidence.
  2. `evaluation_summary.md`: Human-readable Markdown summary report with pillar breakdowns and audio delivery notes.

---

## 📌 Rule 6: Git Commits Executed Only Upon User Request (with Pre-Commit Documentation Audit)
* Run tests/verifications to ensure zero syntax or runtime errors after editing code.
* Only execute `git commit` when the USER explicitly requests/instructs to commit the changes (e.g., "commit changes", "commit current stage").
* **Pre-Commit Documentation Check**: When the user requests to commit, FIRST check if any documentation files (e.g., `model/<stage_folder>/doc/current.md`, `doc/folder_strucuture.md`, `doc/tech_stack.md`, `doc/rule.md`) need to be updated for recent code/schema/architecture changes. If any documentation updates are pending, update those files FIRST before running `git commit`.
* When committing upon user request, use standard Conventional Commit messages:
  - `feat(...)`: New features or UI components
  - `fix(...)`: Bug fixes or error resilience updates
  - `docs(...)`: Documentation updates
  - `chore(...)`: Cleanup or dependency updates

---

## 📌 Rule 7: Immediate Documentation Synchronization
* Whenever code paths, function signatures, input/output schemas, or test directories are altered:
  - Immediately update `model/<stage_folder>/doc/current.md`.
  - Immediately update `doc/folder_strucuture.md`.
  - Never leave documentation outdated relative to actual code implementation.

---

## 📌 Rule 8: Dual-Mode Execution Support (GUI + CLI) & Launcher Synchronization
* Every stage model in `model/` must maintain two execution entry points:
  1. 🖥️ **Kivy Desktop GUI Client (`front.py`)**: Modern glassmorphic desktop interface for interactive user execution across all stages (`research_model`, `question_model`, `voice_to_voice_model`, `reports_model`, `workflow`).
  2. 💻 **Headless CLI Test Harness (`test_pipeline.py`)**: Command-line interface for automated testing and preset verification.
* **Mandatory Launcher Synchronization (`run.bat`)**: Whenever stage execution entry points (GUI/CLI), model scripts, diagnostic utilities, or data cleaning handlers are created or altered, `run.bat` MUST be updated immediately to keep launcher menu options in exact sync with the codebase.

---

## 📌 Rule 9: Error Resilience & Offline Fallbacks
* AI generation calls (Gemini API / Local LLM) must never crash uncaught on rate limits (`429 RESOURCE_EXHAUSTED`) or network disconnects (`RemoteProtocolError`).
* Always wrap external LLM API calls with exponential backoff retries and graceful rule-based offline fallback generators.

---

## 📌 Rule 10: Code Execution Standard & Environment Directives
* **Virtual Environment Required**: Always execute Python scripts, test suites, and code quality tools using the workspace virtual environment (`.\.venv\Scripts\python.exe` or `.\.venv\Scripts\pip.exe`).
* **Root Execution Context**: Always execute scripts and test modules from the `backend/` root directory using module path format (e.g. `.\.venv\Scripts\python.exe -m model.workflow.model.test_pipeline` or `.\.venv\Scripts\python.exe -m model.<stage_folder>.model.test_pipeline`) to guarantee relative imports and `sys.path` resolution succeed across all 4 stages.
* **Interactive Launcher**: Use `run.bat` for interactive GUI/CLI launcher menu options across individual model stages and the full workflow application.
* **Quality & Security Audits**: Execute `.\.venv\Scripts\python.exe scan_code_quality.py` to run automated code quality audits (`ruff`, `pylint`, `mypy`, `bandit`, `radon`).

---

## 📌 Rule 11: Microphone Priority, Resampling & Hardware Configurations
* The audio capture hardware settings in `config.py` (e.g., WASAPI vs DirectSound priorities) and the anti-aliased downsampling fallback logic in `listener.py` (e.g., boxcar decimation `reshape(-1, 3).mean(axis=1)`) have been meticulously tuned for specific Intel Smart Sound Array hardware. 
* **DO NOT** modify, rearrange, or refactor the baseline hardware priorities in `config.py`.
* **Override Support**: If hardware decimation causes audio aliasing (robotic/buzzing voice), users MUST use the `.env` override `MIC_DEVICE_INDEX=0` to force MME/DirectSound. `listener.py` natively supports OS-level 16kHz resampling, which provides perfect voice quality for STT when MME is selected.
* **DC Drift**: Per-chunk DC offset is mitigated by an IIR high-pass filter applied across the entire final utterance buffer before STT. Do not revert to per-chunk mean subtraction.
* If encountering audio issues, focus strictly on the **alignment** of the three core components (`listener.py`, `brain.py`, `speaker.py`), such as barge-in logic, silence thresholds, turn-taking timing, or prompt alignment.
