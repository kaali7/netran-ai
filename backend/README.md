# Netran AI — Multi-Stage AI Technical Interviewer Backend

Netran AI is an intelligent, web-augmented, multimodal AI technical interviewer. The system simulates real-world corporate technical interview loops by combining web-extracted market intelligence, dynamic resume-to-JD cross-matching, continuous real-time voice activity detection (VAD), speech-to-text (STT), local streaming LLM reasoning, neural text-to-speech (TTS), and multimodal audio-grounded candidate evaluation.

---

## 🎯 What We Are Making

The backend architecture comprises **4 core AI model stages** linked by a **Unified Workflow Orchestrator**:

1. **Stage 1 — JD Research & Market Intelligence Engine (`research_model`)**:
   - Parses raw Job Descriptions (JDs), queries live engineering web sources (LeetCode, Glassdoor, GitHub, GeeksforGeeks, Reddit) using **Tavily Search API**, synthesizes assessment rubrics via **Gemini 3.6 Flash**, and caches results in a local **SQLite** database (`cache.db`).

2. **Stage 2 — Contextual Question & Behavioral Prompt Engine (`question_model`)**:
   - Parses candidate resumes (`.pdf`, `.docx`, `.txt`) using `pypdf` and `python-docx`. Performs skill-gap cross-matching against the JD rubric to construct a 15-question tree stratified across 3 difficulty tiers (Junior, Mid, Senior) and generates a 1-2 sentence latency-constrained system prompt for Stage 3.

3. **Stage 3 — Live Voice-to-Voice Streaming Loop (`voice_to_voice_model`)**:
   - Runs a real-time cascaded voice loop powered by **Silero VAD v3** (with inline dynamic noise floor calibration), **Faster-Whisper** (`small` int8 model loaded 100% offline) for STT, offline **SpeechBrain ECAPA-TDNN** (`speechbrain/spkrec-ecapa-voxceleb`) for candidate speaker verification, local **Ollama Qwen2.5:3b** streaming LLM reasoning under the `Eva` interviewer persona, a **Qwen2.5:3B**-powered hybrid turn-taking classifier, and **Kokoro-82M** (`af_bella` voice) neural TTS streaming playback. Continuously records microphone PCM audio (`recording.wav`) and millisecond-precision timing telemetry (`transcript.json`).

4. **Stage 4 — Post-Session Multimodal Evaluation Engine (`reports_model`)**:
   - Slices continuous audio into per-turn WAV clips (`turn_01.wav` ... `turn_15.wav`) based on manifest timestamps and runs a 3-branch **Gemini Multimodal Evaluation Engine** (Audio Branch, Technical Branch, Combine Branch) to output dual evaluation artifacts: `report.json` and `evaluation_summary.md`.

5. **Workflow Orchestrator (`workflow`)**:
   - A unified **6-screen Kivy Desktop Application** (`SetupScreen` → `ResearchScreen` → `QuestionScreen` → `InterviewScreen` → `ReportProcessingScreen` → `ReportScreen`) that connects Stage 1 through Stage 4 in background threads with live UI progress callbacks.

---

## 💻 Prerequisites & System Requirements

### 1. Recommended Python Version
- **Python 3.11 or Python 3.12** (specifically 64-bit Windows) is **strongly recommended**.
- *Why?* Python 3.11/3.12 provides optimum binary wheel compatibility for native C-extension packages used in speech processing and UI rendering (`faster-whisper`, `sounddevice`, `onnxruntime`, `kivy`, `torch`).

Check your active Python version before proceeding:
```cmd
python --version
```

### 2. System Hardware Requirements
- **OS**: Windows 10 / 11 (64-bit).
- **RAM**: 8 GB minimum (16 GB recommended for optimal Whisper + Kokoro + Ollama co-execution).
- **CPU**: Multi-core x86_64 processor (Intel i5/i7, AMD Ryzen 5/7+).
- **Audio Hardware**: Active Microphone and Headphones/Speakers.

### 3. Local Model Engine Requirement: Ollama
Stage 3 uses local Ollama execution for LLM reasoning:
1. Download and install **Ollama** from [ollama.com](https://ollama.com).
2. Ensure Ollama service is running in the background.
3. Open a terminal and pull the Qwen2.5 model:
   ```cmd
   ollama pull qwen2.5:3b
   ```

---

## ⚙️ Installation & Package Setup Guide

Follow these step-by-step instructions to set up the backend environment from scratch:

### Step 1: Open Terminal & Navigate to Backend
```cmd
cd "c:\kali\product\netran ai\backend"
```

### Step 2: Create a Virtual Environment (Python 3.11 or 3.12)
```cmd
py -3.12 -m venv .venv
```
*(Or use `py -3.11 -m venv .venv` if Python 3.11 is installed).*

### Step 3: Activate the Virtual Environment
- **Windows Command Prompt (cmd)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

### Step 4: Upgrade Packaging Tools & Install Requirements
Install all master backend dependencies using the consolidated [`requirements.txt`](file:///c:/kali/product/netran%20ai/backend/requirements.txt):
```cmd
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 5: Configure Environment Credentials (`.env`)
Create or edit the `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GEMINI_MODEL=gemini-3.6-flash
OLLAMA_MODEL=qwen2.5:3b
```

### Step 6: Download / Verify Silero VAD Weights
Run the VAD downloader utility to fetch the `silero_vad.onnx` neural weight file (~2 MB):
```cmd
python -m model.voice_to_voice_model.model.download_vad
```

### Step 7: Download Stage 3 Voice Model Weights (Faster-Whisper, Kokoro, & SpeechBrain)

Stage 3 (`voice_to_voice_model`) relies on 3 Hugging Face neural models for local offline voice interaction:

| Model / Asset | Hugging Face / Source ID | Size | Purpose / Module | Download / Cache Location |
| :--- | :--- | :---: | :--- | :--- |
| **1. Ollama LLM** | `qwen2.5:3b` | ~1.9 GB | Streaming reasoning engine & turn classifier (`brain.py`) | Managed by Ollama service |
| **2. Silero VAD v3** | `silero_vad.onnx` | ~2 MB | Neural voice activity detection (`listener.py`) | `model/voice_to_voice_model/model/silero_vad.onnx` |
| **3. Faster-Whisper** | `Systran/faster-whisper-small` | ~500 MB | Local speech-to-text transcription (`listener.py`) | `%USERPROFILE%\.cache\huggingface\hub\` |
| **4. Kokoro-82M** | `hexgrad/Kokoro-82M` | ~350 MB | Neural text-to-speech engine (`speaker.py`) | `%USERPROFILE%\.cache\huggingface\hub\` |
| **5. SpeechBrain ECAPA** | `speechbrain/spkrec-ecapa-voxceleb` | ~100 MB | Candidate speaker verification (`speaker_verifier.py`) | `%USERPROFILE%\.cache\huggingface\hub\` |

#### Automatic Downloads on First Run:
The first time you launch Stage 3 or hardware diagnostics (`listener.py`, `speaker.py`, `speaker_verifier.py`), the system will automatically download these models to your local Hugging Face cache (`%USERPROFILE%\.cache\huggingface\hub\`).

*Note: You must have an active internet connection during the first run. Subsequent runs execute **100% offline** without any network dependencies (`HF_HUB_OFFLINE=1`).*

#### Manual Pre-Download (Recommended for Offline Environments):
If you want to manually pre-download all Hugging Face models before starting the application, use `huggingface-cli` (included in `requirements.txt`):

```cmd
hf download Systran/faster-whisper-small
hf download hexgrad/Kokoro-82M
hf download speechbrain/spkrec-ecapa-voxceleb
```

---

## 🚀 How to Run

You can launch the backend using either the interactive batch launcher or direct Python module commands.

### Method A: Interactive Launcher (`run.bat`) — Recommended
Run [`run.bat`](file:///c:/kali/product/netran%20ai/backend/run.bat) from the backend directory to open an interactive operational suite:

```cmd
run.bat
```

**Key Menu Options**:
- **Option 1**: Launch Unified 6-Screen Netran AI Interview Workflow (Complete App).
- **Options 2–5**: Run standalone stage models (Stage 1 Research, Stage 2 Question, Stage 3 Voice, Stage 4 Report).
- **Options 6–11**: Run component hardware diagnostics (listener, speaker, brain, turn classifier, question manager, speaker verifier).
- **Options 12–14**: Setup Tools (Install requirements, Download/verify VAD & Hugging Face models, Check system dependencies).
- **Options 15–20**: Maintenance tools (clean test outputs, sessions, cache DB, bytecode trash, full deep clean, code audit scanner).

---

### Method B: Direct Python Module Commands

Make sure your `.venv` is activated, then run:

#### 1. Run Complete Combined 6-Screen Application
```cmd
python -m model.workflow.model.front
```

#### 2. Run Stage 1 (JD Research & Market Intel Desktop GUI)
```cmd
python -m model.research_model.model.front
```

#### 3. Run Stage 2 (Question Tree & System Prompt Generator)
- **Kivy UI**:
  ```cmd
  python -m model.question_model.model.front
  ```
- **CLI Harness**:
  ```cmd
  python -m model.question_model.model.test_pipeline
  ```

#### 4. Run Stage 3 (Standalone Voice Interview Desktop GUI)
```cmd
python -m model.voice_to_voice_model.model.front
```

#### 5. Run Stage 4 (Post-Session Report Generator)
- **Kivy UI**:
  ```cmd
  python -m model.reports_model.model.front
  ```
- **CLI Harness**:
  ```cmd
  python -m model.reports_model.model.test_pipeline
  ```

#### 6. Run System Requirements & Dependency Checker
```cmd
python check_dependencies.py
```

#### 7. Run Code Quality & Architecture Audit Scanner
```cmd
python scan_code_quality.py
```

---

## 🧹 Maintenance & Data Cleaning

During development and testing, temporary test output files and session logs are generated. You can clean these files using `run.bat` or manually:

- **Stage Test Outputs (`model/*/model/test_output/`)**: Stores single-stage test outputs.
- **Session Directories (`model/sessions/`)**: Stores active interview session folders (`sess_<timestamp>/`).
- **SQLite Cache (`model/research_model/model/cache.db`)**: Stores cached JD rubrics.

### Clean Data Commands via `run.bat`:
- Select **Option 15**: Deletes stage `test/output/` and `test/process/` folders.
- Select **Option 16**: Deletes active session folders in `model/sessions/` and `sessions/`.
- Select **Option 17**: Deletes SQLite `cache.db` files.
- Select **Option 18**: Deletes Python bytecode trash (`__pycache__`, `.pyc`), `.log` files, and `_interview_log.txt`.
- Select **Option 19**: Performs a **Full Deep Clean** returning the repository to pristine condition.
- Select **Option 20**: Run Code Quality Audit (Ruff, Bandit, Radon).

---

## 📚 Project Documentation

Additional system documentation is available in the `doc/` directory:
- [`doc/current.md`](file:///c:/kali/product/netran%20ai/backend/doc/current.md): Detailed current operational status & stage synthesis.
- [`doc/folder_strucuture.md`](file:///c:/kali/product/netran%20ai/backend/doc/folder_strucuture.md): Complete directory structure and file inventory.
- [`doc/rule.md`](file:///c:/kali/product/netran%20ai/backend/doc/rule.md): Mandatory architectural rules and agent instructions.
- [`doc/tech_stack.md`](file:///c:/kali/product/netran%20ai/backend/doc/tech_stack.md): Technical framework components.
- [`model/workflow/doc/overall_model_process.md`](file:///c:/kali/product/netran%20ai/backend/model/workflow/doc/overall_model_process.md): High-level multi-stage process matrix.
