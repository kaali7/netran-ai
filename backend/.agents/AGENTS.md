# Workspace Rules for Netran AI Project

Before performing research or modifying any code in this repository:
1. Always read [doc/rule.md](file:///c:/kali/product/netran%20ai/backend/doc/rule.md), [doc/tech_stack.md](file:///c:/kali/product/netran%20ai/backend/doc/tech_stack.md), and [doc/folder_strucuture.md](file:///c:/kali/product/netran%20ai/backend/doc/folder_strucuture.md).
2. Check `model/<stage_folder>/doc/current.md` before editing any code within a specific model stage.
3. Adhere strictly to the Stage 1 output contract (`sess_<timestamp>.json` single file) and Stage 2 dual input/output contracts (`sample_job_detail.json` + `sample_resume.json` -> `sess_<timestamp>/` containing `interview_questions.json` & `interviewer_behavior.json`).
4. Always update documentation when code or schema changes are made.
5. Only execute `git commit` when the USER explicitly requests/instructs to commit. When instructed to commit, ALWAYS check first if any documentation files (`model/<stage_folder>/doc/current.md`, `doc/folder_strucuture.md`, `doc/tech_stack.md`, `doc/rule.md`) need to be updated. If any documentation updates are pending, update those files FIRST before running `git commit`.
6. Always update `run.bat` whenever stage execution entry points (GUI/CLI), model scripts, diagnostics, or data cleaning scripts are modified or added.
7. Always run code/tests from the backend root using the virtual environment (`.\.venv\Scripts\python.exe -m model.<stage>.model.test_pipeline`) or `run.bat`, and run `.\.venv\Scripts\python.exe scan_code_quality.py` for code quality checks (`ruff`, `pylint`, `mypy`, `bandit`, `radon`).
