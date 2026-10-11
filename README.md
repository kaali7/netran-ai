# Netran AI — Autonomous Full-Duplex AI Voice Interview & Evaluation Platform

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Faster-Whisper](https://img.shields.io/badge/STT-Faster--Whisper-orange.svg)](https://github.com/SYSTRAN/faster-whisper)
[![Silero VAD](https://img.shields.io/badge/VAD-Silero%20v3-green.svg)](https://github.com/snakers4/silero-vad)
[![Kokoro TTS](https://img.shields.io/badge/TTS-Kokoro--82M-purple.svg)](https://huggingface.co/hexgrad/Kokoro-82M)
[![Ollama](https://img.shields.io/badge/LLM-Qwen%202.5--3B-black.svg?logo=ollama&logoColor=white)](https://ollama.ai)
[![Gemini](https://img.shields.io/badge/Gemini%20API-3.6%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)

<p align="center">
  <b>Enterprise-grade, real-time, low-latency conversational voice AI platform conducting end-to-end technical interviews, dynamic adaptive branching, and automated multimodal evaluation.</b>
</p>

[Key Features](#-key-features) • [Architecture](#-system-architecture) • [Screenshots & Demo](#-visual-tour--interface) • [Quick Start](#-quick-start-guide) • [Tech Stack](#-technology-stack) • [Documentation](#-documentation-index)

</div>

---

## 📸 Visual Tour & Interface

### 🎥 End-to-End Demonstration Video
> Watch Netran AI conduct a full-duplex conversational voice interview, adapt question difficulty in real time, and generate a post-session evaluation report:
>
> 📹 **[Watch Demo Video](doc/img/demo_video.mp4)** *(File location: `doc/img/demo_video.mp4`)*

---

### 🖥️ Platform Screenshots

<div align="center">

| Candidate Dashboard | Live Full-Duplex Voice Room |
| :---: | :---: |
| ![Candidate Dashboard](doc/img/dashbaord_page.png) | ![Live Voice Room](doc/img/audio_recode_interview.png) |
| *Personalized interview hub, quick practice templates, and performance KPIs* | *Eva AI interviewer avatar, live acoustic waveform, and conversational speech* |

| Multimodal Evaluation Processing | Comprehensive Scorecard & Feedback |
| :---: | :---: |
| ![Evaluation Processing](doc/img/evalution_proces.png) | ![Report Scorecard](doc/img/report_page.png) |
| *Real-time Stage 4 audio slicing and multi-branch assessment* | *Technical accuracy, vocal confidence, delivery pace, and answer breakdown* |

| Performance Analytics & Growth | Interview History & Past Archives |
| :---: | :---: |
| ![Analytics Dashboard](doc/img/analytics_page.png) | ![History Archives](doc/img/history_page.png) |
| *Pillar benchmarks, score progression over time, and skill mastery* | *Past sessions, full transcript replays, audio playback, and score cards* |

</div>

---

## 🌟 Key Features

- 🎙️ **Full-Duplex Voice-to-Voice Loop (Sub-400ms TTFA)**:
  Real-time conversational turn-taking combining **Faster-Whisper** (CTranslate2 int8 STT), **Silero VAD** (Neural Voice Activity Detection), **Kokoro-82M** (Neural TTS), and **Ollama Qwen 2.5 (3B)** local streaming brain.
- 🎯 **Level 2 TurnManager & Playback Synchronization**:
  Deterministic event-driven client synchronization (`playback_started` / `playback_finished` WebSocket control protocol) preventing echo bleed-through and timing jitter across different laptop hardware.
- 🌳 **15-Question Contextual Tree & Adaptive Branching**:
  Stage 2 synthesizes deep job description requirements and candidate resumes into a 15-question tree with automatic strong/weak follow-up branching based on keyword density scoring.
- 📊 **3-Branch Multimodal Evaluation Engine (Stage 4)**:
  Automated post-interview assessment analyzing acoustic waveform metrics (hesitation, pauses, speech pace WPM), technical accuracy, and Gemini-synthesized hiring recommendation reports.
- 🌐 **Tri-Mode Execution Architecture**:
  1. **Web Application (FastAPI + React 18 SPA)**: Modern production web suite with real-time audio streaming.
  2. **Desktop GUI Client (`front.py`)**: Dark-themed Kivy desktop application.
  3. **Headless CLI (`test_pipeline.py`)**: Automated test harness across all 4 stages.
- 🛡️ **Enterprise Security & Data Isolation**:
  Bcrypt password hashing, JWT authorization, SQLAlchemy persistence, input-hash deduplication cache, and LAN-wide cross-origin support.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI WEB GATEWAY                                 │
│  api/main.py • JWT Auth • Sessions • Ingestion • Templates • Live WebSocket WS    │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
    ┌─────────────────────────────────────┼─────────────────────────────────────┐
    ▼                                     ▼                                     ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────┐
│ STAGE 1: Research     │   │ STAGE 2: Questions    │   │ STAGE 3: Voice Loop       │
│ • Tavily Web Search   │──▶│ • Skill Gap Analysis  │──▶│ • Silero VAD (v3 ONNX)    │
│ • Gemini Rubric Gen   │   │ • 15-Question Tree    │   │ • Faster-Whisper (small)  │
│ • SQLite Hash Cache   │   │ • Eva Persona Prompt  │   │ • Level 2 TurnManager     │
└───────────────────────┘   └───────────────────────┘   │ • Ollama Qwen 2.5 (3B)    │
                                                        │ • Kokoro-82M Neural TTS   │
                                                        └─────────────┬─────────────┘
                                                                      │
                                                                      ▼
                                                        ┌───────────────────────────┐
                                                        │ STAGE 4: Evaluation       │
                                                        │ • Turn-by-Turn Slicing    │
                                                        │ • 3-Branch Gemini Analysis│
                                                        │ • Scorecard & PDF Export  │
                                                        └───────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Virtual environment recommended)
- **Node.js 18+** & `npm`
- **Ollama** installed with `qwen2.5:3b` pulled (`ollama run qwen2.5:3b`)
- **Google Gemini API Key** ([Get key here](https://aistudio.google.com))
- **Tavily API Key** ([Get key here](https://tavily.com))

---

### 2. Backend Installation & Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY and TAVILY_API_KEY
```

---

### 3. Voice AI Models Setup (Speaking & Listening Time)

To guarantee sub-400ms low-latency full-duplex voice performance without runtime download delays during live interviews, pre-download the neural models for speaking (TTS), listening (STT), voice activity detection (VAD), and local reasoning:

```bash
# 1. Download Silero VAD, Faster-Whisper, Kokoro TTS, & SpeechBrain weights (Automated)
python -m model.voice_to_voice_model.model.download_vad
# Or select Option 16 in run.bat

# 2. Pull local Ollama reasoning model for Eva's conversational brain
ollama pull qwen2.5:3b
```

#### 📦 Pre-Downloaded Models Summary:

| Model | Purpose / Phase | Source / Hugging Face ID | Size | Execution Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Kokoro-82M** | Eva Neural Speech Synthesis (Speaking) | `hexgrad/Kokoro-82M` | ~82 MB | Local PyTorch / KPipeline (Preheated on server startup) |
| **Faster-Whisper** | Candidate Speech-to-Text (Listening) | `Systran/faster-whisper-small` | ~460 MB | Local CTranslate2 int8 (`HF_HUB_OFFLINE=1`) |
| **Silero VAD v3** | Voice Activity Detection & Gating | `silero_vad.onnx` | ~2.3 MB | Local ONNX Runtime |
| **Qwen 2.5 (3B)** | Conversational Reasoning & Turn-Taking | `ollama run qwen2.5:3b` | ~1.9 GB | Local Ollama streaming daemon |
| **ECAPA-TDNN** | Candidate Voice Print Verification | `speechbrain/spkrec-ecapa-voxceleb` | ~80 MB | Local SpeechBrain embedding extractor |

---

### 4. Frontend Installation & Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start development server
npm run dev
# The client will run at http://localhost:5173
```

---

### 5. Interactive Master Suite Launcher (`run.bat`)

On Windows, execute `run.bat` from the root directory for an all-in-one interactive operational launcher:

```cmd
run.bat
```

The master suite provides one-click options to:
- Launch the FastAPI Web API Server (`uvicorn api.main:app --reload`)
- Launch the React + Vite Web Client (`npm run dev`)
- Run individual stages (Stage 1 Research, Stage 2 Questions, Stage 3 Voice, Stage 4 Reports)
- Run hardware diagnostics (Silero VAD test, Kokoro TTS test, Ollama brain test)
- Perform database resets and deep cache cleaning

---

## 🧰 Technology Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Backend API** | FastAPI / Uvicorn | High-performance asynchronous REST & WebSocket gateway |
| **Frontend Client** | React 18 / Vite | Component-driven SPA with Web Audio API Worklets |
| **Speech-to-Text** | Faster-Whisper (CTranslate2) | Real-time offline int8 transcription with domain vocabulary |
| **Voice Activity Detection** | Silero VAD (v3 ONNX) | Real-time voice gating and streaming DC-blocking filters |
| **Text-to-Speech** | Kokoro-82M (KPipeline) | Sub-250ms high-fidelity neural speech synthesis |
| **Local Reasoning Brain**| Ollama + Qwen 2.5 (3B) | Streaming conversational interviewer dialogue engine |
| **Cloud Synthesis AI** | Google Gemini (3.6 Flash) | Stage 1 market research, Stage 2 question trees, Stage 4 evaluation |
| **Web Intelligence** | Tavily Search API | Real-time market hiring standards and salary benchmarks |
| **Speaker Verification** | SpeechBrain ECAPA-TDNN | Candidate voice print auto-enrollment and identity verification |
| **Database & Cache** | SQLAlchemy / SQLite 3 | Deduplicating SHA-256 fingerprint cache and user session store |

---

## 📂 Project Directory Structure

```
netran-ai/
├── README.md                      # Master root project documentation
├── run.bat                        # Master operational launcher suite
├── requirements.txt               # Unified project Python dependencies
│
├── backend/                       # Backend server & AI engine pipelines
│   ├── .env.example               # Environment variables configuration template
│   ├── scan_code_quality.py       # Code quality audit scanner (ruff, bandit, radon)
│   ├── api/                       # FastAPI Web API Gateway
│   │   ├── main.py                # App entry point, CORS middleware, lifespan preheating
│   │   ├── routers/               # Auth, Setup, Voice, Reports, History, Analytics
│   │   └── services/              # Pipeline adapters and background execution managers
│   └── model/                     # Multi-stage AI pipeline models
│       ├── research_model/        # Stage 1: Market Intelligence & JD Analysis
│       ├── question_model/        # Stage 2: Question Tree & Behavior Synthesis
│       ├── voice_to_voice_model/  # Stage 3: Live Voice-to-Voice Conversational Engine
│       └── reports_model/         # Stage 4: Multimodal Evaluation Engine
│
├── frontend/                      # React 18 + Vite Web Application
│   ├── README.md                  # Frontend architecture & component guide
│   ├── public/pcm-processor.js    # Web Audio API worklet (48kHz -> 16kHz Int16 PCM)
│   └── src/
│       ├── components/            # Reusable UI cards, AvatarEva, Navbars, Audio players
│       ├── hooks/                 # useInterviewSession (WebSocket & audio protocol)
│       └── pages/                 # Dashboard, Interview, Processing, Report, Analytics
│
└── doc/                           # Comprehensive architectural documentation
    ├── img/                       # UI screenshots, diagrams, and demonstration video
    ├── rule.md                    # Mandatory system rules and stage contracts
    ├── tech_stack.md              # Detailed technical stack specifications
    ├── folder_strucuture.md       # Full repository directory inventory
    ├── current.md                 # System status and recent architectural milestones
    ├── web_voice.md               # WebSocket audio protocol and latency optimizations
    └── task_completion.md         # Deliverables matrix and verification log
```

---

## 📚 Documentation Index

For in-depth architectural guides, refer to the documentation in [`doc/`](doc/):
- **[System Directives & Stage Contracts](doc/rule.md)**: Rules, schemas, and I/O contracts.
- **[Full Technology Stack](doc/tech_stack.md)**: Deep-dive into AI models, audio DSP, and DB caching.
- **[Directory & Module Inventory](doc/folder_strucuture.md)**: Comprehensive map of all project files.
- **[Web Voice Architecture & Protocol](doc/web_voice.md)**: AudioWorklet capture, WebSockets, and Level 2 TurnManager synchronization.
- **[Implementation Tracker](doc/task_completion.md)**: Task completion matrix, bug fixes, and verification audit logs.

---

<div align="center">
  <sub>Built with ❤️ by the Netran AI Engineering Team.</sub>
</div>
