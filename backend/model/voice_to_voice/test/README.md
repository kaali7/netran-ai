# Voice-to-Voice AI Interviewer Test Environment

This directory contains the optimized voice-to-voice backend prototype for **Netran AI**. It includes Neural Voice Activity Detection (VAD), an echo-gating mechanism, improved Whisper-based transcription, structured conversation flow control, and latency benchmarks.

---

## Prerequisites

1. **Python Environment**:
   Ensure you use the project's virtual environment located at `backend/.venv/`.
   
2. **Ollama**:
   Make sure Ollama is installed and running locally with the Qwen2.5 model pulled:
   ```bash
   ollama run qwen2.5:1.5b
   ```

3. **Audio Devices**:
   Ensure a working microphone and speakers/headphones are connected to your machine.

---

## Setup & Running

Follow these steps to run the application:

### Step 1: Activate the Virtual Environment
Open a terminal in the project directory (`backend/`) and run:
* **Windows PowerShell**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **Windows Command Prompt**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

### Step 2: Navigate to the Test Directory
```bash
cd model/voice_to_voice/test
```

### Step 3: Download the VAD Model (One-time)
Run the VAD downloader script to fetch the required `silero_vad.onnx` model weight file:
```bash
python download_vad.py
```

### Step 4: Run the Application
Start the Kivy UI client:
```bash
python main_app.py
```
*Click **"Start Interview"** to begin speaking. The interview will automatically close after 15 questions.*

---

## Standalone Verifications

You can test individual pipelines to isolate hardware or driver issues:

* **Test LLM Response Streaming**:
  ```bash
  python brain.py
  ```
* **Test TTS Speech Output**:
  ```bash
  python speaker.py
  ```
* **Test Audio Capture, VAD, and STT**:
  ```bash
  python listener.py
  ```
  *(Note: On its very first run, this will download the Faster-Whisper `small` model weight files which is ~145MB).*

---

## Latency Benchmarking

Every completed conversational turn writes performance metrics to `benchmark_log.csv`:
- `stt_ms`: Transcription speed (from silence detection to text).
- `ttft_ms`: LLM response speed (time-to-first-token).
- `ttfa_ms`: End-to-end latency (from user silence to audio starting to play).
