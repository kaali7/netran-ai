# Workspace Rules for Netran AI Project

Before performing research or modifying any code in this repository:
1. Always read [doc/rule.md](file:///c:/kali/product/netran%20ai/backend/doc/rule.md), [doc/tech_stack.md](file:///c:/kali/product/netran%20ai/backend/doc/tech_stack.md), and [doc/folder_strucuture.md](file:///c:/kali/product/netran%20ai/backend/doc/folder_strucuture.md).
2. Check `model/<stage_folder>/doc/current.md` before editing any code within a specific model stage.
3. Adhere strictly to the Stage 1 output contract (`sess_<timestamp>.json` single file) and Stage 2 dual input/output contracts (`sample_job_detail.json` + `sample_resume.json` -> `sess_<timestamp>/` containing `interview_questions.json` & `interviewer_behavior.json`).
4. Always update documentation when code or schema changes are made.
5. Always run `git add .` and `git commit` after implementing and verifying changes.
