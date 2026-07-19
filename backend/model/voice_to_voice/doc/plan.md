# Netran AI: Cascaded Pipeline Optimization Plan

This document outlines the step-by-step engineering roadmap to optimize the Netran AI voice-to-voice backend. The goal is to achieve sub-1-second time-to-first-audio (TTFA) without changing the core models (Faster-Whisper, Ollama Qwen2.5:1.5b, Kokoro-82M).

---

## 🎯 Architectural Goal
Shift from a sequential blocking architecture to an **overlapping concurrent execution model**. By streaming data between components as soon as it is available, the system will process speech, generate reasoning, and synthesize audio simultaneously.

---

## 🛠️ Phase 1: Sentence Buffer Optimization (The Critical Bridge)
**Target File:** `brain.py`
**Objective:** Prevent the LLM from waiting for the entire response to finish before sending text to the TTS engine. Chunk text logically so the TTS engine has enough context to speak naturally.

### Implementation Steps:
1. **Stream Tokens:** Ensure the `generate_eva_response` function yields tokens continuously via Server-Sent Events (SSE) or generator yields.
2. **Implement the Accumulator:** Create a string buffer that collects these incoming tokens.
3. **Punctuation Splitting Logic:**
   * Scan the buffer for sentence-terminating punctuation: `.`, `!`, `?` followed by a space.
   * **Guard 1 (Minimum Length):** Do not split if the accumulated string is less than 10-15 characters (prevents clipped, unnatural audio like "Yes.").
   * **Guard 2 (Abbreviations):** Implement a regex or exclusion list to ignore standard abbreviations (e.g., `Mr.`, `Dr.`, `e.g.`, `i.e.`) and decimal numbers.
4. **Flush and Route:** Once a valid sentence boundary is detected, yield/return that specific sentence chunk to `speaker.py` and clear it from the buffer while the LLM continues generating the next sentence.

### Expected Outcome:
The TTS engine will begin synthesizing and playing the first sentence while the LLM is still computing the second sentence, drastically reducing perceived latency.

---

## 🎙️ Phase 2: Neural Voice Activity Detection (VAD)
**Target File:** `listener.py`
**Objective:** Replace the fragile amplitude/RMS mathematical checks with a robust, neural-based silence detector to prevent background noise from interrupting the transcription flow.

### Implementation Steps:
1. **Download Silero VAD:** Add the ONNX version of Silero VAD (approx. 2MB) to the backend directory.
2. **Restructure Audio Framing:** 
   * Update the PyAudio input stream to capture strict **32ms chunks** at 16kHz.
   * Pass these specific frames directly to the Silero model.
3. **Probability Thresholds:** Configure the VAD to trigger "speech start" when the probability > 0.5, and "speech end" (triggering the pipeline) when the probability drops below 0.3 for a sustained duration (e.g., 700ms).

### Expected Outcome:
High-accuracy turn-taking. The microphone will instantly know when you stop speaking, ignoring keyboard clacks, breathing, or background room noise.

---

## 🛑 Phase 3: Interruption State Machine (Echo Gate)
**Target Files:** `listener.py` & `speaker.py`
**Objective:** Prevent audio feedback loops where the microphone picks up the AI's voice, and allow the user to interrupt the AI cleanly.

### Implementation Steps:
1. **Global State Management:** Create a shared state flag (e.g., `IS_AGENT_SPEAKING = False`).
2. **Speaker Toggle:**
   * In `speaker.py`, set `IS_AGENT_SPEAKING = True` right before writing the raw PCM audio bytes to the PyAudio output stream.
   * Set it to `False` the moment the audio buffer is completely drained.
3. **Listener Attenuation:**
   * In `listener.py`, wrap the microphone capture loop in an `if` statement checking this flag.
   * If `IS_AGENT_SPEAKING` is `True`, either drop the incoming audio frames entirely or apply a heavy digital attenuation (volume reduction) to prevent the VAD from triggering.
4. **Barge-in Logic (Optional/Advanced):** If the user speaks loudly enough to overcome the attenuation threshold while the agent is speaking, instantly send a "stop" signal to `speaker.py` to flush the output queue and halt the LLM generation.

### Expected Outcome:
Flawless half-duplex communication. The AI will never listen to itself, and the conversation will feel strictly turn-based and clean.

---

## 📊 Phase 4: Measurement and Tuning
**Target File:** `benchmark.py` (New File)
**Objective:** Instrument the codebase to measure exact millisecond improvements and identify bottlenecks.

### Implementation Steps:
1. **Timestamp Wrappers:** Inject `time.perf_counter()` at the start and end of critical functions.
2. **Key Metrics to Track:**
   * **STT Processing Time:** Milliseconds from the moment Silero VAD detects silence to the moment Faster-Whisper outputs the final string.
   * **TTFT (Time-to-First-Token):** Milliseconds from Ollama receiving the prompt to emitting the first text token.
   * **TTFA (Time-to-First-Audio):** The ultimate pipeline metric—milliseconds from user silence to the first speaker audio chunk playing.
3. **Logging:** Write these metrics to a simple CSV or append them to your existing `interview_log.txt` for review.

### Expected Outcome:
Data-driven optimization. You will know exactly which component is slowing down the interaction and can tune chunk sizes and buffers accordingly.

---

## ✅ Completed Implementation Log (Hardware & Model Fixes)
**Location:** `model/voice_to_voice/test/`

During the standalone integration testing of the STT and TTS models on Windows hardware, several critical reliability fixes were implemented:

### Listener Module (`listener.py`)
1. **DC Offset & Auto-Gain:** Standard Windows microphones often capture at extremely low gain (RMS ~0.001) with a DC offset (baseline drift). Mathematical RMS thresholds failed here. We implemented:
   * **DC Offset Removal:** Centers the waveform at 0.0 so the Silero neural network isn't confused by a shifted baseline.
   * **Dynamic Peak Normalization (Auto-Gain):** Dynamically scales incoming audio to a target 90% peak (capped at 50x multiplier) *without* clipping the audio into square waves.
2. **VAD Threshold Tuning:** Due to the hardware auto-gain, Silero VAD confidence scores were lower than studio norms (maxing around 0.12). Thresholds were lowered to `0.05` to successfully detect speech.
3. **Whisper Hallucination Guards:** Added `no_speech_threshold=0.4` and `compression_ratio_threshold=1.5` to Faster-Whisper to stop the model from hallucinating repeated text (e.g., "Hello? Hello?") or initial prompts on near-silent audio.
4. **Caching:** Reverted to the local cached `small` model to ensure 0-second load times.

### Speaker Module (`speaker.py`)
1. **Engine Swap (PyAudio -> sounddevice):** PyAudio's default MME/DirectSound drivers on Windows 11 frequently route audio silently to wrong/virtual devices. The playback engine was rewritten to use `sounddevice.play()`, which leverages modern WASAPI drivers to guarantee output to the default desktop speakers.
2. **Native Float32 Playback:** Kokoro outputs `float32` tensors at 24kHz natively; switching to `sounddevice` allowed us to play these arrays directly without expensive manual `int16` / binary bytes conversion.

### Hotfixes & Stability (`listener.py` v2)
1. **VAD Indentation Bug:** Fixed a critical indentation error where the recording loop was breaking instantly after the first 32ms frame of detected speech, causing Whisper to reject the audio as too short.
2. **Volume Override Failsafe:** Added a hard `RMS > 0.03` failsafe trigger. If the Silero VAD neural network fails to recognize speech (probability near 0.00) but the raw physical volume of the microphone is extremely loud, the loop will bypass the VAD failure and instantly trigger the `has_spoken` state, guaranteeing the microphone captures the user's voice.
3. **Logic Failsafe (`AND` -> `OR`):** Fixed a logical flaw where the loop required both VAD probability `AND` high volume to continue recording. Switched to `OR`, allowing high raw volume to successfully hold the recording open until the user actually stops speaking.