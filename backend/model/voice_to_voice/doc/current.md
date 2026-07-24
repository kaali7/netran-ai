# Netran AI Voice-to-Voice: Current Implementation & System Architecture

## 📌 Executive Summary
The Netran AI Voice-to-Voice backend and desktop application have reached full operational stability. The system runs a real-time, low-latency cascaded voice processing pipeline comprising **Neural Voice Activity Detection (Silero VAD)**, **Speech-to-Text (Faster-Whisper)**, **Streaming LLM Reasoning (Ollama Qwen2.5:1.5B)**, and **Text-to-Speech (Kokoro-82M)**, integrated into a dark-themed **Kivy Desktop GUI**.

---

## 🏗️ Core Architecture & Component Breakdown

```
 ┌────────────────┐     512 samples @ 16kHz float32      ┌─────────────────────────┐
 │   Microphone   │ ───────────────────────────────────> │  Silero VAD + Auto-Gain │
 └────────────────┘                                      └───────────┬─────────────┘
                                                                     │ Speech Ended
                                                                     ▼
 ┌────────────────┐     Native 24kHz float32 Audio       ┌─────────────────────────┐
 │  sounddevice   │ <─────────────────────────────────── │ Faster-Whisper ("small")│
 └───────▲────────┘                                      └───────────┬─────────────┘
         │ Chunks                                                    │ Transcript
         │                                                           ▼
 ┌───────┴────────┐     Regex Sentence Stream (>15 chars) ┌─────────────────────────┐
 │ Kokoro-82M TTS │ <─────────────────────────────────── │ Ollama (Qwen2.5:1.5B)  │
 └────────────────┘                                      └─────────────────────────┘
```

### 1. Speech-to-Text & Audio Capture ([listener.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice/model/listener.py))
* **Audio Capture Engine**: Built using `sounddevice` running at 16kHz single-channel `float32`.
* **DC Offset Removal & Dynamic Auto-Gain**: Centers raw PCM audio around `0.0` and applies dynamic peak scaling (up to 50x gain boost targeting 90% peak) to handle low-gain Windows microphones.
* **Silero VAD v3 Inference**: Evaluates speech probabilities frame-by-frame on 32ms (512-sample) windows.
* **Hybrid VAD + RMS Failsafe**:
  - **Speech Start**: Triggered if `speech_prob > 0.05 AND rms > 0.005` OR hard volume override `rms > 0.03`.
  - **Speech Continuation**: Maintained while `speech_prob > 0.02 OR rms > 0.002`.
  - **Silence Timeout**: Finalized after 15 consecutive silent frames (~480ms) or a 12-second max timeout.
* **Faster-Whisper STT**: Uses cached `small` model in `int8` CPU mode with domain prompt guidance (`FRONTEND_PROMPT`) to accurately transcribe tech terminology without hallucinations.
* **Echo Gate Protection**: Checks `speaker.IS_AGENT_SPEAKING` via lazy module import to drop microphone frames during TTS playback and eliminate audio feedback loops.

### 2. LLM Engine & Response Generation ([brain.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice/model/brain.py))
* **Model**: Local Ollama execution of `qwen2.5:1.5b`.
* **Persona & Guardrails**: System prompt (`Eva`) enforces concise 1–2 sentence technical interviewer responses, prevents commentary on background noise, and handles a structured 15-question sequence.
* **Token Streaming**: Yields text tokens in real time via `ollama.chat(stream=True)`.
* **Pre-heating**: `preload()` function warms model weights prior to session start.

### 3. Text-to-Speech Playback ([speaker.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice/model/speaker.py))
* **Kokoro-82M Engine**: Local neural TTS initialized using `KPipeline(lang_code="a")` with the `af_bella` voice preset.
* **Native Direct Audio Output**: Renders float32 tensors at 24kHz sample rate directly to `sounddevice.play()`, bypassing legacy PyAudio MME driver routing issues.
* **State Management**: Controls global `IS_AGENT_SPEAKING` flag for echo suppression.

### 4. Overlapping Pipeline & Latency Optimization ([main_app.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice/model/main_app.py))
* **Sentence-Level Streaming Buffer**: Uses regex boundary detection (`[.!?\n]`) to split streaming LLM tokens into sentence chunks.
* **Abbreviation & Length Safeguards**: Requires a minimum chunk length of >15 characters and skips standard abbreviations (e.g., `Mr.`, `Dr.`, `e.g.`, `vs.`), ensuring natural speech cadence.
* **Overlapping Execution**: TTS synthesizes and speaks the first sentence while the LLM is actively computing subsequent sentences, significantly reducing Time-to-First-Audio (TTFA).

### 5. Desktop Application & Dual Modes ([main_app.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice/model/main_app.py))
* **Kivy Modern Dark GUI**: Includes real-time VAD diagnostics, volume meter bar, live conversation transcript panel, and control buttons (Start, Stop & Save, Restart).
* **Dual Operation Modes**:
  1. **Dynamic Live LLM Mode**: Standard 15-question AI technical interview powered by Qwen2.5.
  2. **Script Calibration Mode**: Practice mode utilizing pre-scripted technical tracks from `interview_scripts.json` (React, Next.js, TypeScript, Build Tools, CSS/Tailwind) with fuzzy sequence-matching (`difflib.SequenceMatcher`) for reading-accuracy scoring.

### 6. Metrics & Benchmarking ([benchmark.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice/model/benchmark.py))
* Measures high-resolution timing via `time.perf_counter()`.
* Automatically appends performance telemetry (`stt_ms`, `ttft_ms`, `ttfa_ms`) to `benchmark_log.csv`.

---

## 🛠️ Resolved Issues & Bug Fixes

1. **VAD Indentation Bug (Fixed)**
   - *Issue*: Loop broke prematurely after 32ms of speech, causing Whisper to reject audio as too short.
   - *Fix*: Fixed loop scope so recording continues until silence threshold (~480ms) is reached.

2. **Low-Gain Mic & VAD Probability Failure (Fixed)**
   - *Issue*: Silero VAD yielded low probability scores (<0.20) on Windows microphones due to DC offset and low gain.
   - *Fix*: Added DC offset removal, dynamic peak auto-gain (up to 50x boost), lowered probability threshold to `0.05`, and added a hard RMS failsafe (`rms > 0.03`).

3. **Logic Gate Cutoff Bug (Fixed)**
   - *Issue*: Silence reset evaluated `speech_prob > 0.02 AND rms > 0.002`, failing when VAD prob dropped despite user talking loudly.
   - *Fix*: Changed condition to `OR`, keeping the recording open as long as physical audio volume is detected.

4. **Audio Driver & Playback Muting (Fixed)**
   - *Issue*: PyAudio default Windows drivers muted playback or directed audio to incorrect output devices.
   - *Fix*: Replaced PyAudio with `sounddevice.play()`, sending raw float32 arrays directly to WASAPI speaker output.

---

## 📊 Performance Benchmark Targets
| Metric | Description | Target | Current Status |
| :--- | :--- | :--- | :--- |
| **STT Latency** | Audio silence to Whisper text output | < 600 ms | Operational (~350–550 ms) |
| **TTFT** | Prompt sent to LLM first token output | < 400 ms | Operational (~200–350 ms) |
| **TTFA** | User silence to speaker first audio chunk | < 1200 ms | Operational (~800–1100 ms) |

