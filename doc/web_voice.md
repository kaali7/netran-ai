# Web Voice-to-Voice Communication Architecture

This document outlines the architecture, data flow, and critical files involved in the real-time, full-duplex voice-to-voice interview communication between the web frontend and the Netran AI backend.

## 1. Architecture Overview

The system uses a persistent WebSocket connection to stream raw binary audio data (PCM) alongside JSON control messages. This allows for low-latency, bidirectional communication without the overhead of HTTP requests or the complexity of WebRTC.

### Key Components

#### Frontend (React / Web Audio API)
- **Audio Capture (`pcm-processor.js`)**: An `AudioWorkletProcessor` that runs on a separate thread in the browser. It captures raw Float32 microphone data at the native sample rate (e.g., 48kHz) and downsamples/converts it to 16kHz Int16 PCM chunks.
- **Session Manager (`useInterviewSession.js`)**: A custom React hook that manages the `AudioContext`, the WebSocket connection, and coordinates state (e.g., Autoplay suspension, mic permissions, speaking state).
- **Audio Playback**: The backend streams 24kHz Int16 PCM audio chunks to the frontend. The `useInterviewSession` hook receives these binary blobs, decodes them using `audioContext.decodeAudioData`, and plays them sequentially using `AudioBufferSourceNode`.

#### Backend (FastAPI / WebSockets)
- **API Router (`api/routers/voice.py`)**: Accepts the WebSocket connection (`/api/v1/voice/stream/{session_id}`). It creates async queues for incoming and outgoing audio and spans background workers (`recv_worker`, `audio_send_worker`) to drain and send these queues to the WebSocket.
- **Voice Engine (`voice_engine.py`)**: The central loop (`run_interview`) that orchestrates the interview. It manages the state machine, fetching questions, evaluating transcripts, and triggering LLM responses.
- **Listener (`listener.py`)**: Connects to the incoming WebSocket queue via `ws_stream_producer`. It uses Silero VAD to detect speech endpoints and Faster-Whisper to transcribe the candidate's speech.
- **Speaker (`speaker.py`)**: Generates TTS using the Kokoro-82M model. It pushes generated audio chunks into an `audio_out_queue` which the FastAPI router streams back to the frontend.

---

## 2. Critical Files

| Layer | File Path | Purpose |
| :--- | :--- | :--- |
| **Frontend** | `frontend/public/pcm-processor.js` | Web Audio API Worklet. Captures microphone data and converts Float32 to Int16 PCM format. |
| **Frontend** | `frontend/src/hooks/useInterviewSession.js` | Manages the WebSocket, handles browser AudioContext suspension, and orchestrates audio playback. |
| **Frontend** | `frontend/src/pages/Interview.jsx` | The UI layer that displays the Avatar, subtitles, VAD status, and "Enable Audio" overlay. |
| **Backend API** | `backend/api/routers/voice.py` | FastAPI WebSocket endpoint. Bridges the async WebSocket world with the synchronous Python Voice Engine threads. |
| **Backend Model** | `backend/model/voice_to_voice_model/model/voice_engine.py` | The main execution loop of the interview (handles turns, barge-in logic, and state transitions). |
| **Backend Model** | `backend/model/voice_to_voice_model/model/listener.py` | VAD and STT. Drains WebSocket incoming audio queue for transcription. |
| **Backend Model** | `backend/model/voice_to_voice_model/model/speaker.py` | Neural TTS synthesis (Kokoro). Enqueues generated audio to the WebSocket outgoing queue. |

---

## 3. Issues Faced and Solutions Applied (August 2026)

During the integration of the web-based voice room, several critical communication issues were encountered and resolved:

### Issue 1: React 18 Strict Mode Double-Connects
- **Problem**: In development mode, React mounts `useInterviewSession` twice. This opened two simultaneous WebSockets. The backend immediately rejected the second connection and marked the session as `EVALUATING` prematurely, locking the user out.
- **Solution**: Modified `voice.py` to check the `total_turns` completed. If a WebSocket disconnects with 0 turns completed, the backend reverts the session status to `READY` instead of `EVALUATING`, allowing immediate reconnection without locking the session.

### Issue 2: Browser Autoplay Policy Suspending Audio
- **Problem**: Modern browsers (Chrome/Safari) instantly suspend any `AudioContext` created without a direct user interaction on that specific page. Because the dashboard navigation didn't count as a direct interaction on the `/interview/:id` route, the microphone `AudioWorklet` and the speaker playback were silently frozen.
- **Solution**: Implemented `audioState` tracking in `useInterviewSession.js`. If the state is `suspended`, the UI displays a "Click to Enable Audio & Join Interview" overlay button. Clicking this executes `audioContext.resume()`, instantly unfreezing the microphone and allowing the backend's opening greeting to play.

### Issue 3: Retake Session WebSocket Rejections
- **Problem**: When a user clicked "Retake Session" from the Dashboard, the frontend navigated them back to the exact same completed `session_id`. The backend correctly rejected this connection for security, resulting in a silent room.
- **Solution**: Added a new `/duplicate` endpoint in `setup.py` that deep-copies the `parsed_resume`, `parsed_jd`, and `question_tree` into a brand new session ID. Updated `Dashboard.jsx` to call this endpoint, ensuring users always enter a fresh room when retaking.

### Issue 4: Missing Global Imports & Crashes
- **Problem**: The backend threw a `NameError: name 'time' is not defined` inside `speaker.py` when attempting to call `time.monotonic()` during the `wait_until_done()` phase. This crashed the voice engine thread instantly, abruptly closing the WebSocket before any audio could be sent.
- **Solution**: Restored the missing `import time` at the top of `speaker.py`.

### Issue 5: Excessive TTS First-Turn Latency (Kokoro Loading)
- **Problem**: The Kokoro TTS model is heavily lazy-loaded. On the very first interview turn, `_get_pipeline()` blocked for 10-15 seconds to load the AI weights into memory. Users perceived this as a broken connection because the WebSocket was open but silent.
- **Solution**: Hooked `preload_speaker()` into the FastAPI `@asynccontextmanager lifespan` in `api/main.py`. The heavy TTS model is now pre-heated and loaded into RAM the moment the backend server starts, resulting in near-instant audio generation when a user joins the room.

### Issue 6: React 18 Strict Mode `ws.onclose` Race Condition
- **Problem**: In React 18 development mode, `useEffect` executes double-mount (`mount -> unmount -> mount`). The first WebSocket instance (`ws1`) is told to close via cleanup, while the second WebSocket instance (`ws2`) becomes active (`wsRef.current = ws2`). When `ws1` finished closing asynchronously, its `onclose` callback fired and invoked `stopSession()`, which inspected `wsRef.current` and prematurely closed `ws2`. This killed the connection immediately before the user could interact.
- **Solution**: Added an instance check guard in `useInterviewSession.js`:
  ```javascript
  ws.onclose = () => {
    if (wsRef.current && wsRef.current !== ws) {
      return; // Ignore close events from old, discarded WebSocket instances
    }
    // ... proceed with teardown ...
  };
  ```

### Issue 7: Non-blocking Icebreaker Dispatch in Engine Loop
- **Problem**: In `voice_engine.py`, the synchronous turn 0 icebreaker greeting (`speak_text(initial_greeting)`) blocked the execution thread. If any client event or delay occurred during generation, the `while not self.stop_event.is_set()` loop was delayed from starting, causing race conditions in state reporting.
- **Solution**: Spanned the initial icebreaker greeting in a dedicated thread (`threading.Thread(target=speak_text, args=(initial_greeting,)).start()`), allowing the engine to immediately enter the `while` loop, stream microphone capture, and execute Silero VAD detection seamlessly.

---

## 4. Real-time Execution Tracing & Diagnostics

To guarantee end-to-end observability across the full duplex voice pipeline, the `ExecutionLogger` framework records structured JSONL traces (`data/sessions/<session_id>/execution_trace.jsonl`) and echoes them directly to the console during execution:

| Source | Event Types | Details Logged |
| :--- | :--- | :--- |
| `FRONTEND` | `WS_CONNECTED`, `AUDIO_CHUNK_RECEIVED`, `MIC_ACCESS_GRANTED`, `MIC_ACCESS_DENIED`, `WS_ERROR`, `BARGE_IN_TRIGGERED` | Sent from client via `{action: "client_log"}` |
| `BACKEND_API` | `WS_CONNECTED`, `AUDIO_CHUNK_SENT`, `WS_DISCONNECTED` | Audio frame byte sizes, connection lifecycle |
| `BACKEND_ENGINE` | `ENGINE_START`, `PRE_LOOP_CHECK`, `VAD_*`, `STT_START`, `LLM_START`, `TTS_START`, `ENGINE_STOP` | Turn indices, VAD probabilities, RMS, transcripts |
| `PIPELINE_RUNNER` | `PIPELINE_START`, `STEP_START`, `STEP_COMPLETE`, `PIPELINE_COMPLETE` | Resume extraction, JD research, Question generation stages |

---

## 5. Voice Latency & Timing Fixes (August 2026)

A full pipeline audit identified 7 root causes for inconsistent Eva response timing (early cutoffs, ghost triggers, and delayed responses). All 7 have been resolved:

### Fix A — Per-Turn Calibration Caching (`listener.py` + `session_state.py`)
- **Problem**: Every `listen_and_transcribe()` call ran 30 frames × 32ms = **960ms of calibration** at the start of each turn. During calibration, the audio queue was fully drained (garbage flushed). This silently discarded the first ~960ms of the candidate's response on turns 2, 3, 4... The VAD then started mid-sentence with only the trailing audio, quickly triggering "silence reached" and cutting Eva in early.
- **Solution**: Added calibration cache fields to `SessionState` (`calibration_done`, `cached_ambient_floor`, `cached_start_rms_gate`, `cached_continue_rms_gate`, `cached_noise_reducer`). Turn 1 runs calibration and writes results into the cache. Turns 2+ read the cache directly and skip the 960ms window entirely — the audio queue is never drained on cached turns.

### Fix B — Pause Tolerance Raised for Web Mode (`session_state.py` + `listener.py`)
- **Problem**: `pause_tolerance_ms = 800ms` (25 silence frames). WebSocket audio delivery adds ~100–200ms of pipeline buffering through `recv_worker → audio_queue → ws_stream_producer`. Effective VAD silence tolerance was only ~600ms — not enough for natural mid-sentence pauses.
- **Solution**: Raised `pause_tolerance_ms` default to **1200ms**. Also raised `MIN_SPEECH_FRAMES` to **25 (800ms)** in WebSocket mode — endpointing cannot fire on less than 800ms of accumulated speech. Desktop sessions reset to 800ms in the `finally` block.

### Fix C — Disable `noisereduce` for Web Sessions (`listener.py`)
- **Problem**: After the VAD loop finished, the entire audio buffer was passed through `noisereduce.reduce_noise()` before Whisper. For a 10s answer, this ran ~160k samples through CPU-bound Wiener filtering — adding **500ms–1500ms of latency** before STT even started.
- **Solution**: Gated noisereduce behind `ws_audio_queue is None`. The browser already applies `noiseSuppression: true` + `echoCancellation: true` via `getUserMedia`. Web sessions skip noisereduce entirely; desktop sessions retain it.

### Fix D — Whisper Silence Threshold (`listener.py`)
- **Problem**: `hallucination_silence_threshold=2.0` caused Whisper to internally buffer and analyze 2 extra seconds of trailing silence before returning results — adding a consistent **~2s latency hit** to every candidate utterance.
- **Solution**: Lowered to `hallucination_silence_threshold=0.5` in both Whisper call sites in `listener.py`.

### Fix E — Extended Post-TTS Echo Guard for WebSocket Mode (`listener.py`)
- **Problem**: After Eva finishes speaking, a 300ms echo guard suppressed VAD triggers to prevent capturing speaker echo. But browser `AudioContext` buffers ~150–200ms of in-flight audio through the WS pipeline. Eva's own trailing audio was re-entering VAD after the 300ms guard expired, triggering false speech-starts.
- **Solution**: Extended echo guard to **600ms** when `ws_audio_queue is not None`.

### Fix F — Non-Blocking Audio Send Worker (`api/routers/voice.py`)
- **Problem**: `audio_send_worker` used `get_nowait()` + `asyncio.sleep(0.02)` polling — introducing up to **20ms of jitter** per TTS audio chunk before it was forwarded to the WebSocket.
- **Solution**: Replaced with `loop.run_in_executor(None, _blocking_get)` where `_blocking_get` uses `queue.get(timeout=0.05)`. This wakes immediately when data arrives and yields to the event loop naturally when the queue is empty.

### Fix G — Native OS Sample Rate in AudioWorklet (`pcm-processor.js` + `useInterviewSession.js`)
- **Problem**: `AudioContext` was created with `{ sampleRate: 16000 }`, forcing OS-level resampling at the driver. On Chrome (ARM), Safari, and some Windows WASAPI drivers, this introduced phase/alias artifacts that appeared as brief RMS spikes — occasionally triggering false VAD speech-starts on the backend.
- **Solution**: Removed forced `sampleRate: 16000` from `AudioContext`. The `pcm-processor.js` worklet now reads the native OS rate and performs explicit box-car downsampling to 16kHz internally (integer 3:1 ratio for 48kHz, 6:1 for 96kHz, rational approximation for 44.1kHz). This mirrors the `reshape(-1, 3).mean(axis=1)` approach already used in `listener.py`'s desktop path.

---

### Combined Effect on Eva Response Timing

| Before Fixes | After Fixes |
|:---|:---|
| Turn 1: ~960ms calibration + normal latency | Turn 1: ~960ms calibration (only once) |
| Turn 2+: ~960ms calibration discards leading speech | Turn 2+: 0ms overhead, full speech captured from frame 1 |
| Whisper adds ~2s silence buffer per turn | Whisper adds ~0.5s silence buffer per turn |
| noisereduce adds 500–1500ms per long answer | noisereduce skipped for web (browser handles it) |
| echo guard: 300ms (insufficient for browser buffering) | echo guard: Event-driven via `playback_finished` + 150ms guard |
| audio send: up to 20ms jitter per chunk | audio send: immediate on data-ready |
| **Typical delay: 3–5s + variable** | **Target delay: 0.8–1.5s consistent** |

---

## 6. Level 2 Playback Synchronization Protocol (TurnManager & Client Events)

### The Architectural Evolution
In prototype implementations, the backend used a static 600ms post-TTS echo guard timer. While this worked on development machines, it failed across different laptops due to hardware driver buffering differences, variable network transit jitter, or CPU scheduling variations.

The Level 2 architecture establishes an explicit bidirectional contract:

```text
Backend (voice_engine)                     Frontend (useInterviewSession)
      │                                                │
      ├─────── TTS Audio Chunks Streamed ─────────────►│
      │                                                │
      │   (source.start called)                        ├─► "playback_started" (turn_id)
      │◄─────── JSON: playback_started ────────────────┤
      │ [State: PLAYBACK_ACTIVE]                       │
      │                                                │
      │   (all audio buffers drain from Web Audio API) ├─► "playback_finished" (turn_id)
      │◄─────── JSON: playback_finished ───────────────┤
      │ [State: ECHO_GUARD -> LISTENING]               │
      │                                                │
      │ (VAD active; candidate speaks)                 │
      │◄─────── Binary Mic PCM Chunks ─────────────────┤
```

### Event Specifications
1. **`playback_started`**: Sent when the first scheduled `AudioBufferSourceNode` begins outputting sound.
2. **`playback_finished`**: Sent after the last queued `AudioBufferSourceNode` invokes `onended` (debounced by 180ms).
3. **`DEVICE_INFO`**: Sent once upon microphone stream acquisition, reporting native sample rate, track settings, and platform string.

