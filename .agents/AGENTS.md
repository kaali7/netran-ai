# Workspace Rules for Netran AI Project

Before performing research or modifying any code in this repository:
1. Always read [doc/rule.md](file:///c:/kali/product/netran%20ai/backend/doc/rule.md), [doc/tech_stack.md](file:///c:/kali/product/netran%20ai/backend/doc/tech_stack.md), and [doc/folder_strucuture.md](file:///c:/kali/product/netran%20ai/backend/doc/folder_strucuture.md).
2. Check `model/<stage_folder>/doc/current.md` before editing any code within a specific model stage.
3. Adhere strictly to the Stage 1 output contract (`sess_<timestamp>.json` single file) and Stage 2 dual input/output contracts (`sample_job_detail.json` + `sample_resume.json` -> `sess_<timestamp>/` containing `interview_questions.json` & `interviewer_behavior.json`).
4. Always update documentation when code or schema changes are made.
5. Only execute `git commit` when the USER explicitly requests/instructs to commit. When instructed to commit, ALWAYS check first if any documentation files (`model/<stage_folder>/doc/current.md`, `doc/folder_strucuture.md`, `doc/tech_stack.md`, `doc/rule.md`) need to be updated. If any documentation updates are pending, update those files FIRST before running `git commit`.
6. Always update `run.bat` whenever stage execution entry points (GUI/CLI), model scripts, diagnostics, or data cleaning scripts are modified or added.
7. Always run code/tests from the backend root using the virtual environment (`.\.venv\Scripts\python.exe -m model.<stage>.model.test_pipeline`) or `run.bat`, and run `.\.venv\Scripts\python.exe scan_code_quality.py` for code quality checks (`ruff`, `pylint`, `mypy`, `bandit`, `radon`).
8. When designing or writing code for the frontend, use the appropriate UI/UX skills located in `.agents/skills` based on the specific requirements.
9. Always use the specific design guidelines outlined in `DESIGN.md` for frontend development.
10. When making frontend-related changes, always run frontend code quality scanning and build verification (`npm run build` inside `frontend/`) to ensure zero syntax, bundling, or interface errors.
11. Whenever any code task, bug fix, or feature is completed, always edit and update `doc/task_completion.md` to keep the task completion matrix, verification logs, and pending roadmap items synchronized.
12. **Iconography Standard**: In the frontend project, ONLY use vector icon libraries from the approved list (`Lucide Icons`, `Font Awesome`, `Heroicons`, `Iconify`, `Flaticon`, `Tabler Icons`). Do NOT use raw text emojis for UI icons or structural design elements. Limit emoji usage strictly to rare text-content exceptions.
