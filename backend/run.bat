@echo off
title Netran AI - Backend & Model Operations Suite

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
echo             NETRAN AI - BACKEND MODEL OPERATIONAL SUITE
echo ===================================================================
echo.
echo  --- COMBINED PIPELINE ---
echo   1. Launch Unified 5-Screen Netran AI Interview Workflow (Kivy Desktop)
echo.
echo  --- INDIVIDUAL STAGE MODELS ---
echo   2. Run Stage 1: JD Research ^& Market Intelligence Engine
echo   3. Run Stage 2: Contextual Question Tree ^& Prompt Engine
echo   4. Run Stage 3: Voice-to-Voice Interview Loop
echo   5. Run Stage 4: Post-Session Multimodal Report Generator Engine
echo.
echo  --- COMPONENT HARDWARE DIAGNOSTICS ---
echo   6. Test Speech-to-Text ^& Silero VAD (listener.py)
echo   7. Test Text-to-Speech Kokoro-82M (speaker.py)
echo   8. Test Ollama Qwen2.5 Streaming Brain (brain.py)
echo.
echo  --- SETUP TOOLS ---
echo   9. Install / Update Backend Dependencies (requirements.txt)
echo  10. Download / Verify Silero VAD Model Weights (download_vad.py)
echo.
echo  --- MAINTENANCE ^& DATA CLEANING ---
echo  11. Clean Stage Test Output Directories (model/*/test/output/ ^& model/*/model/test_output/)
echo  12. Clean Generated Session Artifacts (model/sessions/ ^& sessions/)
echo  13. Clean SQLite Research Cache Database (cache.db)
echo  14. Clean Python Bytecode Trash ^& Temporary Logs (__pycache__, *.pyc, *.log)
echo  15. PERFORM FULL DEEP CLEAN (Test Outputs + Sessions + Cache DB + Trash)
echo.
echo   0. Exit
echo ===================================================================
set /p choice="Enter your choice (0-15): "

if "%choice%"=="1" goto run_unified_workflow
if "%choice%"=="2" goto run_research_model
if "%choice%"=="3" goto run_question_model_cli
if "%choice%"=="4" goto run_voice_model
if "%choice%"=="5" goto run_report_model
if "%choice%"=="6" goto test_listener
if "%choice%"=="7" goto test_speaker
if "%choice%"=="8" goto test_brain
if "%choice%"=="9" goto install_reqs
if "%choice%"=="10" goto run_vad
if "%choice%"=="11" goto clean_test_outputs
if "%choice%"=="12" goto clean_sessions
if "%choice%"=="13" goto clean_cache_db
if "%choice%"=="14" goto clean_bytecode_trash
if "%choice%"=="15" goto clean_full_deep
if "%choice%"=="0" goto end
goto menu

:: ── COMBINED PIPELINE ────────────────────────────────────────────────

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

:: ── INDIVIDUAL STAGES ────────────────────────────────────────────────

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

:: ── COMPONENT DIAGNOSTICS ───────────────────────────────────────────

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

:: ── SETUP TOOLS ─────────────────────────────────────────────────────

:install_reqs
echo.
echo [SETUP] Installing / Updating Backend Dependencies from requirements.txt...
.venv\Scripts\python.exe -m pip install -r requirements.txt
pause
goto menu

:run_vad
echo.
echo [SETUP] Downloading / Verify Silero VAD ONNX model weights...
.venv\Scripts\python.exe -m model.voice_to_voice_model.model.download_vad
pause
goto menu

:: ── MAINTENANCE & DATA CLEANING ─────────────────────────────────────

:clean_test_outputs
echo.
echo [CLEANING] Deleting single-stage test output directories...
powershell -Command "Get-ChildItem -Path 'model' -Recurse -Directory -Filter 'output' | Where-Object { $_.Parent.Name -eq 'test' } | Get-ChildItem -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
powershell -Command "Get-ChildItem -Path 'model' -Recurse -Directory -Filter 'test_output' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
echo Clean complete: Stage test output directories removed.
pause
goto menu

:clean_sessions
echo.
echo [CLEANING] Deleting generated session directories (model/sessions ^& sessions)...
if exist "model\sessions" powershell -Command "Remove-Item -Path 'model\sessions\*' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "sessions" powershell -Command "Remove-Item -Path 'sessions\*' -Recurse -Force -ErrorAction SilentlyContinue"
echo Clean complete: Session directories purged.
pause
goto menu

:clean_cache_db
echo.
echo [CLEANING] Deleting SQLite research cache database (cache.db)...
if exist "model\research_model\model\cache.db" del /f /q "model\research_model\model\cache.db"
echo Clean complete: SQLite cache.db deleted.
pause
goto menu

:clean_bytecode_trash
echo.
echo [CLEANING] Removing Python bytecode trash, __pycache__, logs, and benchmark files...
powershell -Command "Get-ChildItem -Path '.' -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
powershell -Command "Get-ChildItem -Path '.' -Recurse -File -Include '*.pyc','*.pyo','*.log','benchmark_log.csv' | Remove-Item -Force -ErrorAction SilentlyContinue"
echo Clean complete: Python bytecode and temporary logs removed.
pause
goto menu

:clean_full_deep
echo.
echo ===================================================================
echo [DEEP CLEAN] Purging ALL test data, sessions, cache DB, and trash...
echo ===================================================================
powershell -Command "Get-ChildItem -Path 'model' -Recurse -Directory -Filter 'output' | Where-Object { $_.Parent.Name -eq 'test' } | Get-ChildItem -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
powershell -Command "Get-ChildItem -Path 'model' -Recurse -Directory -Filter 'test_output' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
if exist "model\sessions" powershell -Command "Remove-Item -Path 'model\sessions\*' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "sessions" powershell -Command "Remove-Item -Path 'sessions\*' -Recurse -Force -ErrorAction SilentlyContinue"
if exist "model\research_model\model\cache.db" del /f /q "model\research_model\model\cache.db"
powershell -Command "Get-ChildItem -Path '.' -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
powershell -Command "Get-ChildItem -Path '.' -Recurse -File -Include '*.pyc','*.pyo','*.log','benchmark_log.csv' | Remove-Item -Force -ErrorAction SilentlyContinue"
echo.
echo DEEP CLEAN COMPLETE: System returned to pristine condition!
pause
goto menu

:end
echo.
echo Exiting Netran AI Operational Suite. Goodbye!
exit /b 0
