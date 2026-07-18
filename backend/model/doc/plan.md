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