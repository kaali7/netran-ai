@echo off
title Netran AI Voice Interview Test Menu

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend/.venv/
    echo Please make sure you have created the .venv.
    pause
    exit /b 1
)

:: Navigate to the test directory
cd model\voice_to_voice\test

:menu
cls
echo ===================================================
echo     NETRAN AI - VOICE-TO-VOICE TEST INTERACTION
echo ===================================================
echo.
echo  1. Run Full Kivy Interview Client (main_app.py)
echo  2. Test Speech-to-Text Listener (listener.py)
echo  3. Test Text-to-Speech Speaker (speaker.py)
echo  4. Test Conversation LLM Brain (brain.py)
echo  5. Download/Verify Silero VAD (download_vad.py)
echo  6. Exit
echo.
echo ===================================================
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto test_listener
if "%choice%"=="3" goto test_speaker
if "%choice%"=="4" goto test_brain
if "%choice%"=="5" goto run_vad
if "%choice%"=="6" goto end
goto menu

:run_app
echo.
echo Starting Kivy Interview Window...
..\..\..\.venv\Scripts\python.exe main_app.py
pause
goto menu

:test_listener
echo.
echo Running Speech-to-Text VAD / Transcription standalone test...
..\..\..\.venv\Scripts\python.exe listener.py
pause
goto menu

:test_speaker
echo.
echo Running Kokoro TTS standalone test...
..\..\..\.venv\Scripts\python.exe speaker.py
pause
goto menu

:test_brain
echo.
echo Running LLM/Ollama standalone test...
..\..\..\.venv\Scripts\python.exe brain.py
pause
goto menu

:run_vad
echo.
echo Downloading/Verifying Silero VAD ONNX model...
..\..\..\.venv\Scripts\python.exe download_vad.py
pause
goto menu

:end
echo Exiting test suite.
exit /b 0
