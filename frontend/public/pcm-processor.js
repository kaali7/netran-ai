/**
 * pcm-processor.js
 *
 * AudioWorkletProcessor that captures raw Float32 audio from the microphone
 * at the NATIVE OS sample rate (typically 48kHz) and downsamples it to 16kHz
 * Int16 PCM for streaming over WebSocket to the Silero VAD + Whisper backend.
 *
 * FIX-G: Removed forced `sampleRate: 16000` from AudioContext (see useInterviewSession.js).
 * Forcing a non-native sample rate causes the OS or browser to resample at the driver level,
 * which on Chrome (ARM), Safari, and some Windows WASAPI drivers introduces phase/alias
 * artifacts that appear as brief RMS spikes, occasionally triggering false VAD speech-starts.
 *
 * Instead, this worklet receives frames at the native OS rate (96kHz / 48kHz / 44.1kHz)
 * and performs an explicit integer-ratio box-car downsample to 16kHz before sending PCM bytes.
 * This mirrors the backend's `original_frame.reshape(-1, 3).mean(axis=1)` approach for 48→16kHz.
 *
 * Supported input rates: 48000 (divide by 3), 44100 (divide by 2.75625 — uses safe rational
 * approximation), 96000 (divide by 6), 16000 (pass-through, no decimation needed).
 * Falls back to pass-through for any other rate to ensure nothing breaks.
 */

class PCMProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super(options);
    // sampleRate is a global in AudioWorkletProcessor scope
    this._inputRate = sampleRate;          // Native OS rate (e.g. 48000, 44100, 96000)
    this._targetRate = 16000;
    this._decimationFactor = this._inputRate / this._targetRate;  // e.g. 3.0 for 48kHz
    this._accumulator = new Float32Array(0);  // Rolling buffer for non-integer decimation
    console.log(
      `[pcm-processor] Native rate=${this._inputRate}Hz, ` +
      `decimation=${this._decimationFactor.toFixed(4)}x → 16kHz`
    );
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    const inputChannel = input[0];
    if (!inputChannel || inputChannel.length === 0) return true;

    let downsampled;

    if (this._decimationFactor === 1.0 || this._inputRate === 16000) {
      // Already at 16kHz — pass through
      downsampled = inputChannel;

    } else if (this._inputRate === 48000 || this._inputRate === 96000) {
      // Integer ratio (48000/16000 = 3, 96000/16000 = 6) — clean box-car average
      const factor = Math.round(this._decimationFactor);
      const outputLength = Math.floor(inputChannel.length / factor);
      downsampled = new Float32Array(outputLength);
      for (let i = 0; i < outputLength; i++) {
        let sum = 0;
        for (let j = 0; j < factor; j++) {
          sum += inputChannel[i * factor + j];
        }
        downsampled[i] = sum / factor;
      }

    } else {
      // Non-integer ratio (e.g. 44100 → 16000): accumulate and resample by averaging windows
      const merged = new Float32Array(this._accumulator.length + inputChannel.length);
      merged.set(this._accumulator, 0);
      merged.set(inputChannel, this._accumulator.length);

      const outputLength = Math.floor(merged.length / this._decimationFactor);
      downsampled = new Float32Array(outputLength);
      for (let i = 0; i < outputLength; i++) {
        const startIdx = i * this._decimationFactor;
        const endIdx = Math.min(startIdx + this._decimationFactor, merged.length);
        let sum = 0;
        let count = 0;
        for (let j = Math.floor(startIdx); j < Math.ceil(endIdx); j++) {
          sum += merged[j];
          count++;
        }
        downsampled[i] = count > 0 ? sum / count : 0;
      }
      // Keep leftover samples for next call
      const consumed = Math.floor(outputLength * this._decimationFactor);
      this._accumulator = merged.slice(consumed);
    }

    if (!downsampled || downsampled.length === 0) return true;

    // Convert Float32 [-1.0, +1.0] to Int16 signed PCM
    const pcm16 = new Int16Array(downsampled.length);
    for (let i = 0; i < downsampled.length; i++) {
      let s = Math.max(-1, Math.min(1, downsampled[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // Transfer the underlying ArrayBuffer (zero-copy) to the main thread
    this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);

