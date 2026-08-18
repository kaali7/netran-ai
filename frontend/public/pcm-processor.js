/**
 * pcm-processor.js
 * 
 * AudioWorkletProcessor that receives raw Float32 audio from the microphone
 * (resampled by the browser's AudioContext to 16kHz) and converts it to
 * 16-bit Mono PCM (Int16Array) bytes to be streamed over WebSocket.
 */

class PCMProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    
    if (input && input.length > 0) {
      const inputChannel = input[0];
      const pcm16 = new Int16Array(inputChannel.length);
      
      for (let i = 0; i < inputChannel.length; i++) {
        // Clamp the float value between -1.0 and +1.0
        let s = Math.max(-1, Math.min(1, inputChannel[i]));
        // Scale to 16-bit signed integer range
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      
      // Transfer the underlying ArrayBuffer to the main thread
      this.port.postMessage(pcm16.buffer);
    }
    
    // Return true to keep the processor alive
    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
