@echo off
title Netran AI Test and Model Menu

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend/.venv/
    echo Please make sure you have created the .venv.
    pause
    exit /b 1
)

:menu
cls
echo ===================================================
echo     NETRAN AI - MODEL AND SYSTEM TEST SUITE
echo ===================================================
echo.
echo  1. Run JD Research and Market Intel Model (Research Engine)
echo  2. Run Full Kivy Interview Client (Voice-to-Voice)
echo  3. Test Speech-to-Text Listener (listener.py)
echo  4. Test Text-to-Speech Speaker (speaker.py)
echo  5. Test Conversation LLM Brain (brain.py)
echo  6. Download/Verify Silero VAD (download_vad.py)
echo  7. Install Research Model Requirements
echo  8. Exit
echo.
echo ===================================================
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto run_research_model
if "%choice%"=="2" goto run_app
if "%choice%"=="3" goto test_listener
if "%choice%"=="4" goto test_speaker
if "%choice%"=="5" goto test_brain
if "%choice%"=="6" goto run_vad
if "%choice%"=="7" goto install_reqs
if "%choice%"=="8" goto end
goto menu

:run_research_model
echo.
echo Starting JD Research and Market Intelligence Engine (Kivy UI)...
cd model\research_model
..\..\.venv\Scripts\python.exe -m model.app
cd ..\..
pause
goto menu


:install_reqs
echo.
echo Installing research model requirements...
.venv\Scripts\python.exe -m pip install -r model\research_model\model\requirements.txt
pause
goto menu

:run_app
echo.
echo Starting Kivy Voice Interview Window...
cd model\voice_to_voice\test
..\..\..\.venv\Scripts\python.exe main_app.py
cd ..\..\..
pause
goto menu

:test_listener
echo.
echo Running Speech-to-Text VAD / Transcription standalone test...
cd model\voice_to_voice\test
..\..\..\.venv\Scripts\python.exe listener.py
cd ..\..\..
pause
goto menu

:test_speaker
echo.
echo Running Kokoro TTS standalone test...
cd model\voice_to_voice\test
..\..\..\.venv\Scripts\python.exe speaker.py
cd ..\..\..
pause
goto menu

:test_brain
echo.
echo Running LLM/Ollama standalone test...
cd model\voice_to_voice\test
..\..\..\.venv\Scripts\python.exe brain.py
cd ..\..\..
pause
goto menu

:run_vad
echo.
echo Downloading/Verifying Silero VAD ONNX model...
cd model\voice_to_voice\test
..\..\..\.venv\Scripts\python.exe download_vad.py
cd ..\..\..
pause
goto menu

:end
echo Exiting test suite.
exit /b 0


