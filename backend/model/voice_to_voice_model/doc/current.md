# Netran AI Voice-to-Voice: Current Implementation & System Architecture

## 📌 Executive Summary
The Netran AI Voice-to-Voice backend and desktop application have reached full operational stability. The system runs a real-time, low-latency cascaded voice processing pipeline comprising **Neural Voice Activity Detection (Silero VAD)**, **Speech-to-Text (Faster-Whisper)**, **Streaming LLM Reasoning (Ollama Qwen2.5:1.5B)**, and **Text-to-Speech (Kokoro-82M)**, integrated into a dark-themed **Kivy Desktop GUI**.

Additionally, Stage 3 continuous microphone recording and millisecond-precision session manifest logging (Plan B) are fully integrated to store session artifacts in `backend/sessions/<session_id>/` for downstream evaluation engines.

---

## 🏗️ Core Architecture & Component Breakdown

```
 ┌────────────────┐     512 samples @ 16kHz float32      ┌─────────────────────────┐
 │   Microphone   │ ───────────────────────────────────> │  Silero VAD + Auto-Gain │
 └───────┬────────┘                                      └───────────┬─────────────┘
         │ Continuous Frames                                         │ Speech Ended
         ▼                                                           ▼
 ┌────────────────┐     Native 24kHz float32 Audio       ┌─────────────────────────┐
 │ Continuous Mic │ <─────────────────────────────────── │ Faster-Whisper ("small")│
 │ Writer (.wav)  │                                      └───────────┬─────────────┘
 └────────────────┘                                                  │ Transcript
                                                                     ▼
 ┌────────────────┐     Regex Sentence Stream (>15 chars) ┌─────────────────────────┐
 │ Kokoro-82M TTS │ <─────────────────────────────────── │ Ollama (Qwen2.5:1.5B)  │
 └────────────────┘                                      └───────────┬─────────────┘
                                                                     │
                                                                     ▼
                                                         ┌─────────────────────────┐
                                                         │  SessionLogger Manifest │
                                                         │ (session_manifest.json) │
                                                         └─────────────────────────┘
```

### 1. Speech-to-Text & Continuous Audio Capture ([listener.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/listener.py))
* **Audio Capture Engine**: Built using `sounddevice` running at 16kHz single-channel `float32`.
* **Per-Frame DC Offset + Auto-Gain Pipeline**: Applied to every frame immediately after mic read — before `ContinuousMicWriter`, before VAD, and before Whisper accumulation.
  - DC offset removal: centers raw PCM around `0.0`.
  - Dynamic peak auto-gain: up to **50x boost targeting 90% peak**, resolving quiet recordings on low-gain Windows Intel microphone arrays.
  - Final utterance-level normalization: re-centers and caps at 10x before Whisper to smooth per-frame gain variation.
  - **Confirmed fix**: `demo_raw.wav` diagnostic confirmed clear audio via this pipeline.
* **Continuous Mic Writer (`ContinuousMicWriter`)**: Writes **gain-boosted** 16kHz 16-bit Mono WAV frames asynchronously. Recordings in `test/output/sess_<timestamp>/recording.wav` now sound clear (not quiet/silent).
* **Silero VAD v3 Inference**: Evaluates speech probabilities frame-by-frame on 32ms (512-sample) windows.
* **Hybrid VAD + RMS Failsafe**:
  - **Speech Start**: Triggered if `speech_prob > 0.10 AND rms > 0.005` OR hard volume override `rms > 0.025`.
  - **Speech Continuation**: Maintained while `speech_prob > 0.05 AND rms > 0.004` (noise-gated — background noise below 0.004 no longer prevents silence detection).
  - **Silence Timeout**: Finalized after **10 consecutive silent frames (~320ms)** (reduced from 480ms for snappy endpointing).
  - **Manual Endpointing**: `trigger_speech_done()` global flag allows instant bypass of silence timer.
* **Faster-Whisper STT**: Uses cached `small` model in `int8` CPU mode with domain prompt guidance (`WHISPER_INITIAL_PROMPT`). VAD silence duration reduced to 300ms for faster processing.
* **Echo Gate Protection**: Checks `speaker.IS_AGENT_SPEAKING` via lazy module import to drop microphone frames during TTS playback.

### 2. LLM Engine & Response Generation ([brain.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/brain.py))
* **Model**: Local Ollama execution of `qwen2.5:1.5b`.
* **Persona & Guardrails**: System prompt (`Eva`) enforces concise 1–2 sentence technical interviewer responses, prevents commentary on background noise, and handles a structured 15-question sequence.
* **Token Streaming**: Yields text tokens in real time via `ollama.chat(stream=True)`.
* **Pre-heating**: `preload()` function warms model weights prior to session start.

### 3. Text-to-Speech Playback ([speaker.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/speaker.py))
* **Kokoro-82M Engine**: Local neural TTS initialized using `KPipeline(lang_code="a")` with the `af_bella` voice preset.
* **Native Direct Audio Output**: Renders float32 tensors at 24kHz sample rate directly to `sounddevice.play()`, bypassing legacy PyAudio MME driver routing issues.
* **State Management**: Controls global `IS_AGENT_SPEAKING` flag for echo suppression.

### 4. Session Manifest & Timestamp Logging ([session_logger.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/session_logger.py))
* **Monotonic Session Timer**: Uses `time.perf_counter()` to eliminate system clock drift.
* **Per-Turn Manifest Data**: Records millisecond timestamps (`audio_start_sec`, `audio_end_sec`), initial hesitation duration (`silence_duration_before_answer_sec`), STT latency (`stt_latency_ms`), TTFT latency (`ttft_ms`), question text, and candidate transcript.
* **Manifest Finalization**: Atomically writes `session_manifest.json` inside `backend/sessions/<session_id>/` upon session stop or completion.

### 5. Overlapping Pipeline & Latency Optimization ([main_app.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/main_app.py))
* **Sentence-Level Streaming Buffer**: Uses regex boundary detection (`[.!?\n]`) to split streaming LLM tokens into sentence chunks.
* **Abbreviation & Length Safeguards**: Requires a minimum chunk length of >15 characters and skips standard abbreviations (e.g., `Mr.`, `Dr.`, `e.g.`, `vs.`), ensuring natural speech cadence.
* **Overlapping Execution**: TTS synthesizes and speaks the first sentence while the LLM is actively computing subsequent sentences, significantly reducing Time-to-First-Audio (TTFA).

### 6. Desktop Application & Dual Execution Modes ([main_app.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/main_app.py) & [test_pipeline.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/test_pipeline.py))
* **Preset Test Inputs (`model/voice_to_voice_model/test/input/`)**:
  - Ingests `interview_questions.json` (Stage 2 question tree) and `interviewer_behavior.json` (Eva persona guidelines & prompt).
  - Presets: `sample_backend/`, `sample_frontend/`, `sample_fullstack/`.
* **Output Session Directory (`model/voice_to_voice_model/test/output/sess_<timestamp>/`)**:
  - `recording.wav`: Continuous raw PCM/WAV candidate & interviewer mic audio.
  - `transcript.json` / `session_manifest.json`: Turn-by-turn dialogue transcript with timestamp & latency telemetry (`stt_ms`, `llm_ms`, `tts_ms`).
* **Dual Execution Modes**:
  1. 🖥️ **Kivy Modern Dark GUI Client (`main_app.py`)**: Visual interactive application with real-time VAD diagnostics, volume meter, live transcript panel, and control buttons:
     - **`⚡ Done Speaking`** button: Triggers `trigger_speech_done()` for instant manual speech endpointing.
     - **`limit_selector` Spinner**: Switch between `Fast Testing (5 Questions)`, `Real-Time Live (15 Questions)`, or `Extended Live (10 Questions)` — default is 5 for test time.
  2. 💻 **Headless CLI Test Harness (`test_pipeline.py`)**: CLI for automated 5-question bounded testing and preset verification.

### 7. Metrics & Benchmarking ([benchmark.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/benchmark.py))
* Measures high-resolution timing via `time.perf_counter()`.
* Automatically appends performance telemetry (`stt_ms`, `ttft_ms`, `ttfa_ms`) to `benchmark_log.csv`.

---

## 🛠️ Resolved Issues & Bug Fixes

1. **VAD Indentation Bug (Fixed)**
   - *Issue*: Loop broke prematurely after 32ms of speech, causing Whisper to reject audio as too short.
   - *Fix*: Fixed loop scope so recording continues until silence threshold is reached.

2. **Low-Gain Mic & VAD Probability Failure (Fixed)**
   - *Issue*: Silero VAD yielded low probability scores (<0.20) on Windows microphones due to DC offset and low gain.
   - *Fix*: Added DC offset removal, dynamic peak auto-gain (up to 50x boost), lowered probability threshold to `0.10`, and added a hard RMS failsafe (`rms > 0.025`).

3. **Logic Gate Cutoff Bug (Fixed)**
   - *Issue*: Silence reset evaluated `speech_prob > 0.02 AND rms > 0.002`, failing when VAD prob dropped despite user talking loudly.
   - *Fix*: Changed to `speech_prob > 0.05 AND rms > 0.004` — noise-gated so background noise (below 0.004) no longer blocks silence detection.

4. **Audio Driver & Playback Muting (Fixed)**
   - *Issue*: PyAudio default Windows drivers muted playback or directed audio to incorrect output devices.
   - *Fix*: Replaced PyAudio with `sounddevice.play()`, sending raw float32 arrays directly to WASAPI speaker output.

5. **Quiet/Silent `recording.wav` Session Artifacts (Fixed)**
   - *Issue*: `ContinuousMicWriter` was saving raw un-amplified mic frames. Intel mic arrays have very low raw signal (RMS ≈ 0.00004), so all session recordings sounded silent/quiet.
   - *Fix*: DC offset + auto-gain pipeline (up to 50x) now applied to every frame **before** writing to `mic_writer` AND before Whisper STT. Confirmed via `demo.py` diagnostic.

6. **VAD Endpointing Hanging After Answer (Fixed)**
   - *Issue*: After finishing speaking, the system waited up to 480ms before processing, sometimes waiting much longer due to background noise resetting silence counter.
   - *Fix*: Silence window reduced to 320ms (10 frames). Added `trigger_speech_done()` + `⚡ Done Speaking` UI button for instant manual bypass.

7. **`Benchmark` Module Import Error (Fixed)**
   - *Issue*: `from benchmark import Benchmark` inline import in `main_app.py` failed when run as a package module.
   - *Fix*: Added robust try/except fallback import chain at top-level of `main_app.py`.

---

## 📊 Performance Benchmark Targets
| Metric | Description | Target | Current Status |
| :--- | :--- | :--- | :--- |
| **STT Latency** | Audio silence to Whisper text output | < 600 ms | Operational (~350–550 ms) |
| **TTFT** | Prompt sent to LLM first token output | < 400 ms | Operational (~200–350 ms) |
| **TTFA** | User silence to speaker first audio chunk | < 1200 ms | Operational (~800–1100 ms) |

