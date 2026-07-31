# Netran AI — Technical Stack Architecture

This document defines the complete technology stack powering **Netran AI**, an autonomous, real-time AI-powered technical interviewer platform.

---

## 🏗️ Core Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │    Kivy Desktop GUI / Web Frontend Client    │
                      └──────────────────────┬───────────────────────┘
                                             │  HTTP REST / WebSockets
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │         FastAPI Backend Web Server           │
                      │    (Python 3.12 + Uvicorn + Asyncio)       │
                      └──────┬───────────────┬───────────────┬───────┘
                             │               │               │
                             ▼               ▼               ▼
┌──────────────────────────────┐ ┌──────────────────────┐ ┌──────────────────────────────┐
│ Stage 1: Market Intelligence │ │ Stage 2: Question    │ │ Stage 3 & 4: Voice Loop &    │
│  (Gemini API + Web Scraping) │ │    Engine (Gemini)    │ │   Local Neural Engines       │
└──────────────────────────────┘ └──────────────────────┘ └──────────────────────────────┘
```

---

## ⚡ 1. Backend Service Layer

* **Web Framework**: **FastAPI**
  * High-performance, asynchronous Python web framework built on **Starlette** and **ASGI** (Uvicorn).
  * Auto-generates OpenAPI (Swagger UI) documentation at `/docs`.
  * Asynchronous endpoint handlers (`async def`) for concurrent voice streaming and LLM pipeline operations.
  * Real-time bidirectional streaming communication using **WebSockets**.
* **Data Validation & Serialization**: **Pydantic v2**
  * Type-safe runtime data validation and schema enforcement (`BaseModel`).
  * Automatic JSON parsing and strict type conversion across API contracts.
* **Server Execution**: **Uvicorn / Hypercorn**
  * Lightning-fast ASGI web server implementation.

---

## 🧠 2. Artificial Intelligence & LLM Stack

* **Primary Cloud Intelligence**: **Google Gemini API (`google-genai` SDK v1.0)**
  * **Model**: `gemini-3.6-flash`
  * **Stage 1 (JD Research & Intelligence Engine)**: Deep structural breakdown of Job Descriptions, tech stack requirement extraction, and trusted web domain scraping synthesis.
  * **Stage 2 (Question & Prompt Engine)**: Generates 15-question stratified interview trees paired with custom latency-tuned system prompts for the **Eva** interviewer persona.
* **Local Neural Brain (Offline LLM Engine)**: **Ollama + Qwen 2.5 (1.5B)**
  * Low-latency streaming response generation during live interview conversations.
  * Zero external API cost and full privacy compliance.
* **Speech-to-Text (STT)**: **Faster-Whisper (CTranslate2 / OpenAI Whisper)**
  * Real-time streaming candidate voice transcription with GPU/CPU acceleration.
* **Voice Activity Detection (VAD)**: **Silero VAD (v4/v5 ONNX Runtime)**
  * Ultra-low-latency speech start/stop detection (`listener.py`), processing audio chunks in microsecond frames.
* **Text-to-Speech (TTS)**: **Kokoro-82M (ONNX / PyTorch)**
  * High-fidelity, ultra-fast neural speech synthesis for the **Eva** interviewer persona with sub-200ms latency (`speaker.py`).

---

## 🎨 3. Client & Presentation Layer

* **Desktop Application**: **Kivy 2.3 GUI**
  * Cross-platform Python UI framework leveraging OpenGL/GLEW hardware acceleration.
  * Custom **Glassmorphic Design System** with dark obsidian theme (`#0D0F17`), smooth rounded cards, and responsive layouts.
  * Thread-safe UI updates integrated with Kivy's main event loop using `Clock.schedule_once`.

---

## 🌐 4. Web Intelligence & Scraping Engine

* **HTTP Client**: **httpx / requests**
  * Asynchronous HTTP requests with connection pooling and SSL verification.
* **HTML Parsing**: **BeautifulSoup4 / lxml**
  * Context extraction from technical career sites, documentation pages, and developer portals.
* **Trusted Intelligence Sources**:
  * LinkedIn (`linkedin.com`), StackOverflow, GitHub, Medium, Dev.to, LeetCode, Glassdoor, Reddit, GeeksforGeeks.
* **Local Caching**: **SQLite 3 (`cache.db`)**
  * SHA-256 query hashed caching mechanism to avoid duplicate web lookups and reduce latency to 0ms.

---

## 📄 5. Document Ingestion & Parsing

* **PDF Parsing**: **PyPDF / pypdf**
  * Automatic text extraction from candidate PDF resumes.
* **Word Document Parsing**: **python-docx**
  * Text and structure extraction from `.docx` resumes.

---

## 🛠️ 6. Development & DevOps Tooling

* **Runtime Environment**: Python 3.12+ (Virtual environment `.venv`)
* **Interactive Command Script**: `run.bat` (Windows automated launcher for CLI test harnesses, GUI apps, hardware diagnostics, cache management, and quality audits)
* **Automated Code Quality & Security Audit Suite**:
  * **Ruff**: Ultra-fast Linter and Code Formatter.
  * **Pylint**: Static code analyzer checking coding standards.
  * **Mypy**: Static type checker enforcing Python 3.10+ type safety.
  * **Bandit**: Automated security audit scanner identifying AST vulnerability patterns.
  * **Radon**: Cyclomatic Complexity (`cc`) and Maintainability Index (`mi`) telemetry analyzer.
  * **Audit Launcher Script**: `scan_code_quality.py` (Automated backend quality scanner executing Ruff, Pylint, Mypy, Bandit, and Radon).
* **Version Control**: Git & GitHub
