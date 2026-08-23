@echo off
title Netran AI - Master Operational Suite

:: Change execution directory to backend
cd /d "%~dp0backend"

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend/.venv/
    echo Please create the virtual environment before launching.
    pause
    exit /b 1
)

:menu
cls
echo ===================================================================
echo             NETRAN AI - MASTER OPERATIONAL SUITE
echo ===================================================================
echo.
echo  --- BACKEND API, CLIENT ^& WORKFLOW RUNNERS ---
echo   1. Launch FastAPI Web API Server (uvicorn api.main:app --reload)
echo   2. Launch React + Vite Web Frontend Client (npm run dev)
echo   3. Launch Unified 6-Screen Netran AI Interview Workflow (Kivy Desktop)
echo.
echo  --- INDIVIDUAL STAGE MODELS ---
echo   4. Run Stage 1: JD Research ^& Market Intelligence Engine
echo   5. Run Stage 2: Contextual Question Tree ^& Prompt Engine
echo   6. Run Stage 3: Voice-to-Voice Interview Loop
echo   7. Run Stage 4: Post-Session Multimodal Report Generator Engine
echo.
echo  --- COMPONENT HARDWARE DIAGNOSTICS ---
echo   8. Test Speech-to-Text ^& Silero VAD (listener.py)
echo   9. Test Text-to-Speech Kokoro-82M (speaker.py)
echo  10. Test Ollama Qwen2.5 Streaming Brain (brain.py)
echo  11. Test Hybrid Turn Classifier (turn_classifier.py)
echo  12. Test Conversation State Manager (question_manager.py)
echo  13. Test Speaker Verifier (speaker_verifier.py)
echo.
echo  --- SETUP TOOLS ---
echo  14. Install / Update Backend Dependencies (requirements.txt)
echo  15. Install / Update Frontend Dependencies (npm install in frontend)
echo  16. Download / Verify Silero VAD Model Weights (download_vad.py)
echo  17. Check System Requirements ^& Dependencies (check_dependencies.py)
echo.
echo  --- MAINTENANCE ^& DATA CLEANING ---
echo  18. Clean Stage Test Output Directories (model/*/test/output/ ^& model/*/test/process/)
echo  19. Clean All Session Directories (backend\data\sessions, model\sessions, sessions)
echo  20. Clean SQLite Cache ^& App Databases (data\cache.db, model\*\cache.db)
echo  21. Reset Full Backend Database ^& Web Sessions (data\cache.db + data\sessions)
echo  22. Clean Python Bytecode Trash ^& Temporary Logs (__pycache__, *.pyc, *.log)
echo  23. PERFORM FULL DEEP CLEAN (Test Outputs + Sessions + DB + Trash)
echo  24. Run Code Quality Audit (scan_code_quality.py)
echo.
echo   0. Exit
echo ===================================================================
set /p choice="Enter your choice (0-24): "

if "%choice%"=="1" goto run_fastapi_server
if "%choice%"=="2" goto run_frontend_vite
if "%choice%"=="3" goto run_unified_workflow
if "%choice%"=="4" goto run_research_model
if "%choice%"=="5" goto run_question_model_cli
if "%choice%"=="6" goto run_voice_model
if "%choice%"=="7" goto run_report_model
if "%choice%"=="8" goto test_listener
if "%choice%"=="9" goto test_speaker
if "%choice%"=="10" goto test_brain
if "%choice%"=="11" goto test_classifier
if "%choice%"=="12" goto test_manager
if "%choice%"=="13" goto test_verifier
if "%choice%"=="14" goto install_reqs
if "%choice%"=="15" goto install_frontend_deps
if "%choice%"=="16" goto run_vad
if "%choice%"=="17" goto check_deps
if "%choice%"=="18" goto clean_test_outputs
if "%choice%"=="19" goto clean_sessions
if "%choice%"=="20" goto clean_cache_db
if "%choice%"=="21" goto clean_full_db_sessions
if "%choice%"=="22" goto clean_bytecode_trash
if "%choice%"=="23" goto clean_full_deep
if "%choice%"=="24" goto run_quality_audit
if "%choice%"=="0" goto end

goto menu

:: ----- BACKEND API GATEWAY -----

:run_fastapi_server
echo.
echo [FASTAPI] Launching Netran AI Web API Gateway Server (http://localhost:8000)...
.venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
goto menu

:run_frontend_vite
echo.
echo [FRONTEND] Launching React + Vite Development Server (http://localhost:5173)...
cd /d "%~dp0frontend"
call npm run dev
cd /d "%~dp0backend"
pause
goto menu

:install_frontend_deps
echo.
echo [FRONTEND SETUP] Installing/Updating Frontend npm dependencies...
cd /d "%~dp0frontend"
call npm install
cd /d "%~dp0backend"
pause
goto menu

:: ----- COMBINED PIPELINE -----

:run_unified_workflow
echo.
echo [LAUNCHING] Complete Unified 4-Stage Netran AI Interview Workflow...
echo  1. Kivy Desktop GUI Client (front.py)
echo  2. Headless CLI Test Harness (test_pipeline.py)
set /p wchoice="Select execution mode (1-2, default 1): "
if "%wchoice%"=="2" (
    .venv\Scripts\python.exe -m model.workflow.model.test_pipeline
) else (
    .venv\Scripts\python.exe -m model.workflow.model.front
)
pause
goto menu

:: ----- INDIVIDUAL STAGES -----

:run_research_model
echo.
echo [LAUNCHING] Stage 1: JD Research ^& Market Intelligence Engine...
echo  1. Kivy Desktop GUI Client (front.py)
echo  2. Headless CLI Test Harness (test_pipeline.py)
set /p rchoice="Select execution mode (1-2, default 1): "
if "%rchoice%"=="2" (
    .venv\Scripts\python.exe -m model.research_model.model.test_pipeline
) else (
    .venv\Scripts\python.exe -m model.research_model.model.front
)
pause
goto menu

:run_question_model_cli
echo.
echo [LAUNCHING] Stage 2: Contextual Question ^& Behavioral Prompt Engine...
echo  1. Kivy Desktop GUI Client (front.py)
echo  2. Headless CLI Test Harness (test_pipeline.py)
set /p qchoice="Select execution mode (1-2, default 1): "
if "%qchoice%"=="2" (
    .venv\Scripts\python.exe -m model.question_model.model.test_pipeline
) else (
    .venv\Scripts\python.exe -m model.question_model.model.front
)
pause
goto menu

:run_voice_model
echo.
echo [LAUNCHING] Stage 3: Live Voice-to-Voice Streaming Loop...
echo  1. Kivy Desktop GUI Client (front.py)
echo  2. Headless CLI Test Harness (test_pipeline.py)
set /p vchoice="Select execution mode (1-2, default 1): "
if "%vchoice%"=="2" (
    .venv\Scripts\python.exe -m model.voice_to_voice_model.model.test_pipeline
) else (
    .venv\Scripts\python.exe -m model.voice_to_voice_model.model.front
)
pause
goto menu

:run_report_model
echo.
echo [LAUNCHING] Stage 4: Post-Session Multimodal Evaluation ^& Report Engine...
echo  1. Kivy Desktop GUI Client (front.py)
echo  2. Headless CLI Test Harness (test_pipeline.py)
set /p repchoice="Select execution mode (1-2, default 1): "
if "%repchoice%"=="2" (
    .venv\Scripts\python.exe -m model.reports_model.model.test_pipeline
) else (
    .venv\Scripts\python.exe -m model.reports_model.model.front
)
pause
goto menu

:: ----- COMPONENT DIAGNOSTICS -----

:test_listener
echo.
echo [TESTING] Speech-to-Text ^& Silero VAD Capture...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.listener
pause
goto menu

:test_speaker
echo.
echo [TESTING] Kokoro-82M Text-to-Speech Playback...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.speaker
pause
goto menu

:test_brain
echo.
echo [TESTING] Ollama Qwen2.5 Conversation Brain...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.brain
pause
goto menu

:test_classifier
echo.
echo [TESTING] Hybrid Turn Classifier...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.turn_classifier
pause
goto menu

:test_manager
echo.
echo [TESTING] Conversation State Manager...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.question_manager
pause
goto menu

:test_verifier
echo.
echo [TESTING] Speaker Verifier (ECAPA-TDNN Enrollment ^& Verification)...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.speaker_verifier
pause
goto menu

:: ----- SETUP TOOLS -----

:install_reqs
echo.
echo [SETUP] Installing / Updating Backend Dependencies from requirements.txt...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
pause
goto menu

:run_vad
echo.
echo [SETUP] Downloading / Verify Silero VAD ONNX model weights...
.\.venv\Scripts\python.exe -m model.voice_to_voice_model.model.download_vad
pause
goto menu

:check_deps
echo.
echo [SETUP] Checking System Requirements ^& Dependencies...
.\.venv\Scripts\python.exe check_dependencies.py
pause
goto menu

:: ----- MAINTENANCE & DATA CLEANING -----

:clean_test_outputs
echo.
echo [CLEANING] Deleting stage test output ^& workflow process directories...
powershell -NoProfile -Command "Remove-Item -Path 'model\*\test\output\*', 'model\*\test\process\*' -Recurse -Force -ErrorAction SilentlyContinue"
echo Clean complete: Stage test output ^& process directories removed.
pause
goto menu

:clean_sessions
echo.
echo [CLEANING] Deleting all active ^& legacy session directories (data\sessions, model\sessions, sessions)...
if exist "data\sessions" powershell -NoProfile -Command "Get-ChildItem -Path 'data\sessions' -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
if exist "model\sessions" powershell -NoProfile -Command "Remove-Item -Path 'model\sessions' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "sessions" powershell -NoProfile -Command "Remove-Item -Path 'sessions' -Recurse -Force -ErrorAction SilentlyContinue"
echo Clean complete: All session directories cleared.
pause
goto menu

:clean_cache_db
echo.
echo [CLEANING] Deleting SQLite research cache ^& app databases (cache.db)...
if exist "data\cache.db" del /f /q "data\cache.db"
if exist "model\research_model\model\cache.db" del /f /q "model\research_model\model\cache.db"
if exist "model\question_model\model\cache.db" del /f /q "model\question_model\model\cache.db"
echo Clean complete: SQLite cache.db files deleted.
pause
goto menu

:clean_full_db_sessions
echo.
echo ===================================================================
echo [RESET BACKEND DB ^& SESSIONS] Resetting database and active sessions...
echo ===================================================================
if exist "data\cache.db" del /f /q "data\cache.db"
if exist "data\sessions" powershell -NoProfile -Command "Get-ChildItem -Path 'data\sessions' -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
if exist "model\sessions" powershell -NoProfile -Command "Remove-Item -Path 'model\sessions' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "sessions" powershell -NoProfile -Command "Remove-Item -Path 'sessions' -Recurse -Force -ErrorAction SilentlyContinue"
echo.
echo Initializing clean database tables...
.\.venv\Scripts\python.exe -c "from api.db import init_db; init_db(); print('Clean database initialized!')"
echo.
echo Backend SQLite DB (data\cache.db) and sessions (data\sessions) have been fully reset!
pause
goto menu

:clean_bytecode_trash
echo.
echo [CLEANING] Removing Python bytecode trash, __pycache__, logs, and _interview_log.txt files...
powershell -NoProfile -Command "Get-ChildItem -Path '.' -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Get-ChildItem -Path '.' -Recurse -File -Include '*.pyc','*.pyo','*.log','_interview_log.txt' | Remove-Item -Force -ErrorAction SilentlyContinue"
echo Clean complete: Python bytecode and temporary logs removed.
pause
goto menu

:clean_full_deep
echo.
echo ===================================================================
echo [DEEP CLEAN] Purging ALL test data, sessions, database, and trash...
echo ===================================================================
powershell -NoProfile -Command "Remove-Item -Path 'model\*\test\output\*', 'model\*\test\process\*' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "data\sessions" powershell -NoProfile -Command "Get-ChildItem -Path 'data\sessions' -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
if exist "model\sessions" powershell -NoProfile -Command "Remove-Item -Path 'model\sessions' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "sessions" powershell -NoProfile -Command "Remove-Item -Path 'sessions' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "data\cache.db" del /f /q "data\cache.db"
if exist "model\research_model\model\cache.db" del /f /q "model\research_model\model\cache.db"
if exist "model\question_model\model\cache.db" del /f /q "model\question_model\model\cache.db"
powershell -NoProfile -Command "Get-ChildItem -Path '.' -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Get-ChildItem -Path '.' -Recurse -File -Include '*.pyc','*.pyo','*.log','_interview_log.txt' | Remove-Item -Force -ErrorAction SilentlyContinue"
echo.
echo Initializing pristine SQLite database...
.\.venv\Scripts\python.exe -c "from api.db import init_db; init_db(); print('Pristine database ready!')"
echo.
echo DEEP CLEAN COMPLETE: System, databases (data\cache.db), and sessions (data\sessions) returned to pristine condition!
pause
goto menu

:run_quality_audit
echo.
echo [QUALITY AUDIT] Running Ruff, Bandit, and Radon Code Quality Scanners...
.\.venv\Scripts\python.exe scan_code_quality.py
pause
goto menu

:end

echo.
echo Exiting Netran AI Operational Suite. Goodbye!
exit /b 0
