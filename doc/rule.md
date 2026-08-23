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
  3. `interviewer_behavior.json`: Object containing `session_id`, `persona` ("Eva"), `target_company`, `candidate_name`, `target_role`, `interviewer_system_prompt`, low-latency voice streaming `behavior_rules`, and STT-enhancing `whisper_domain_vocabulary`.

---

## 📌 Rule 4: Stage 3 (Voice-to-Voice Model) I/O Contract
* **Inputs**: Loaded from `model/voice_to_voice_model/test/input/`:
  - `interview_questions.json` (Question tree from Stage 2)
  - `interviewer_behavior.json` (Eva interviewer persona & system prompt from Stage 2)
* **Outputs**: Dedicated session directory `model/voice_to_voice_model/test/output/sess_<timestamp>/` containing:
  1. `recording.wav`: Continuous raw PCM/WAV candidate & interviewer mic audio.
  2. `transcript.json`: Turn-by-turn dialogue transcript with timestamp & latency telemetry (`stt_ms`, `llm_ms`, `tts_ms`).
* **Question Limit Scoping**:
  - **Testing Time**: Bounded to **5 questions max** (`MAX_QUESTIONS = 5`) for fast automated test harness execution.
  - **Real-Time Live Interview Time**: Supports **10 to 15 questions** (`MAX_QUESTIONS = 10..15`) tailored to job description requirements.

---

## 📌 Rule 5: Stage 4 (Reports Model) Dual I/O Contract
* **Inputs**: Loaded from `model/reports_model/test/input/sample_session/` or active session directory:
  - `continuous_mic_input.wav` / `recording.wav` (Continuous audio recording from Stage 3)
  - `transcript.json` (Per-turn millisecond timing telemetry from Stage 3)
* **Outputs**: Dedicated session directory `model/reports_model/test/output/sess_<timestamp>/` containing:
  1. `report.json`: Machine-readable Pydantic JSON report payload containing technical scores & vocal confidence.
  2. `evaluation_summary.md`: Human-readable Markdown summary report with pillar breakdowns and audio delivery notes.

---

## 📌 Rule 6: Git Commits Executed Only Upon User Request (with Pre-Commit Documentation Audit)
* Run tests/verifications to ensure zero syntax or runtime errors after editing code.
* Only execute `git commit` when the USER explicitly requests/instructs to commit the changes (e.g., "commit changes", "commit current stage").
* **Pre-Commit Documentation Check**: When the user requests to commit, FIRST check if any documentation files (e.g., `doc/current.md`, `doc/backend_plan.md`, `doc/frontend_structure.md`, `doc/folder_strucuture.md`, `doc/tech_stack.md`, `doc/rule.md`, `doc/task_completion.md`) need to be updated for recent code/schema/architecture changes. If any documentation updates are pending, update those files FIRST before running `git commit`.
* **Mandatory Task Completion Logging**: Whenever the user explicitly instructs to "commit the current stage" or "commit changes", you MUST update the `doc/task_completion.md` file to log a verification and sync record of the tasks you just completed BEFORE executing the `git commit`.
* When committing upon user request, use standard Conventional Commit messages:
  - `feat(...)`: New features or UI components
  - `fix(...)`: Bug fixes or error resilience updates
  - `docs(...)`: Documentation updates
  - `chore(...)`: Cleanup or dependency updates

---

## 📌 Rule 7: Immediate Documentation & Task Completion Synchronization
* Whenever code paths, function signatures, input/output schemas, or test directories are altered:
  - Immediately update `doc/current.md` and related architecture plans (`doc/backend_plan.md`, `doc/frontend_structure.md`).
  - Immediately update `doc/folder_strucuture.md`.
  - Never leave documentation outdated relative to actual code implementation.
* **Mandatory Task Completion Update**: Whenever any coding task, bug fix, or feature is completed, you MUST edit and update `doc/task_completion.md` to reflect the latest completed deliverables, verification logs, and active status matrix.

---

## 📌 Rule 8: Tri-Mode Execution Architecture (Web + GUI + CLI) & Launcher Synchronization
* The system supports three primary execution interfaces:
  1. 🌐 **Web Application (FastAPI + React 18 SPA)**: The primary production interface. Full-stack execution via `backend/api/main.py` gateway and `frontend/` React client.
  2. 🖥️ **Legacy Desktop GUI Client (`front.py`)**: Maintained in `model/workflow/` for isolated desktop execution and visual testing.
  3. 💻 **Headless CLI Test Harness (`test_pipeline.py`)**: Command-line interface for automated testing and preset verification across individual stages.
* **Mandatory Launcher Synchronization (`run.bat`)**: Whenever stage execution entry points (Web/GUI/CLI), model scripts, diagnostic utilities, or data cleaning handlers are created or altered, `run.bat` MUST be updated immediately to keep launcher menu options in exact sync with the codebase.

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
* **DC Drift**: DC offset is mitigated by a streaming IIR high-pass filter applied per-frame BEFORE Silero VAD. The filter carries state across chunks for temporal continuity. Do not revert to per-chunk mean subtraction.
* If encountering audio issues, focus strictly on the **alignment** of the three core components (`listener.py`, `brain.py`, `speaker.py`), such as barge-in logic, silence thresholds, turn-taking timing, or prompt alignment.

---

## 📌 Rule 12: Frontend Design and Skill Utilization
* When designing or writing code for the frontend, you MUST use the specialized UI/UX skills available in `.agents/skills/` based on the specific requirement:
  - **`add-ui`**: Use when creating new UI components, sections, pages, or redesigning existing ones to generate multiple production-grade variations.
  - **`animate`**: Use when asked to build new animations, transitions, or add motion to components from scratch.
  - **`brand`**: Use for injecting brand voice, visual identity standards, messaging frameworks, or color palette consistency.
  - **`critique`**: Use for high-level UX/UI evaluation, assessing visual hierarchy, cognitive load, and overall design quality.
  - **`design-taste-frontend`**: Use to establish core design architecture, anti-slop guidelines, typography choices, and layout conventions for landing pages or redesigns.
  - **`improve-animations`**: Use for auditing existing animations across the codebase to create a prioritized roadmap of fixes.
  - **`review-animations`**: Use for reviewing motion code diffs and ensuring animations meet high craft standards.
  - **`slides`**: Use when designing strategic HTML presentations or pitch decks with data visualization.
  - **`ui-ux-pro-max`**: Use for granular UI/UX design intelligence, spacing, accessibility, interaction patterns, responsive layouts, or tech-stack-specific implementation guidance.
  - **`web-design-guidelines`**: Use to audit UI code against Web Interface Guidelines for best practices and accessibility compliance.
* You MUST reference and adhere to the specific design system and aesthetic guidelines defined in `DESIGN.md` (e.g., Modern Glassmorphism, Manrope typography, fluid card-based grid) when making frontend UI changes.

---

## 📌 Rule 13: Frontend Code Quality & Verification Scanning
* Whenever making frontend-related modifications (components, pages, styles, assets, dependencies):
  - **Build & Quality Scan**: Always run `npm run build` in the `frontend/` directory to scan and verify zero compilation, type, bundle, or missing asset errors.
  - **Interface Audit**: Utilize frontend design & auditing skills (`web-design-guidelines`, `ui-ux-pro-max`, `critique`) to review UI quality, accessibility compliance, and visual craft prior to completing work.

---

## 📌 Rule 14: Immediate Task Completion Matrix Synchronization
* Whenever any code task, bug fix, feature, or rule update is completed, you MUST immediately edit and update `doc/task_completion.md` to keep the task completion matrix, verification logs, and pending roadmap items synchronized.

---

## 📌 Rule 15: Frontend Iconography Standard
* **Approved Icon Libraries**: `Lucide Icons` (default for React components), `Font Awesome`, `Heroicons`, `Iconify`, `Flaticon`, `Tabler Icons`.
* **No Raw Text Emojis in UI Design**: Do NOT use raw text emojis (e.g. 🚀, 🎙️, 👋, ⚙️, 🎨, 🤖) as UI icons, section headers, card symbols, or button adornments.
* **Usage Policy**: Always render icons using proper SVG vector components from the approved icon libraries with structured sizing (`size={16..24}`), stroke widths (`strokeWidth={2}`), and harmonious color tokens (`var(--primary)`, `var(--on-surface-variant)`). Limit emoji usage strictly to rare text-content exceptions.

