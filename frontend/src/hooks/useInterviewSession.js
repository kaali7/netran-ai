import { useState, useEffect, useRef, useCallback } from 'react';
import useAuth from './useAuth';

export const useInterviewSession = (sessionId) => {
  const { token } = useAuth();
  
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('connecting'); // 'connecting' | 'connected' | 'disconnected' | 'error'
  const [micPermissionDenied, setMicPermissionDenied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('Initializing interview session...');
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(15);
  const [isSessionDone, setIsSessionDone] = useState(false);
  const [micVolume, setMicVolume] = useState(0);
  const [vadState, setVadState] = useState('Mic: Offline');
  const [audioState, setAudioState] = useState('suspended');
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const isPausedRef = useRef(false);
  const audioContextRef = useRef(null);
  const workletNodeRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const analyserRef = useRef(null);
  const volumeIntervalRef = useRef(null);
  
  // TTS Playback state
  const nextStartTimeRef = useRef(0);
  const sourceNodesQueueRef = useRef([]);
  const speakingDebounceTimerRef = useRef(null);
  const pendingQuestionRef = useRef(null);

  const sendClientLog = useCallback((eventType, details = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({
          action: 'client_log',
          event_type: eventType,
          details: details
        }));
      } catch (e) {
        // Ignore WS errors if closing
      }
    }
  }, []);

  const connectWebSocket = useCallback(() => {
    if (!sessionId || !token) return;

    let baseUrl = import.meta.env.VITE_API_URL || '/api/v1';
    let wsUrl = '';
    
    if (baseUrl.startsWith('http')) {
      wsUrl = baseUrl.replace(/^http/, 'ws') + `/voice/stream/${sessionId}?token=${token}`;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const path = baseUrl.startsWith('/') ? baseUrl : `/${baseUrl}`;
      wsUrl = `${protocol}//${window.location.host}${path}/voice/stream/${sessionId}?token=${token}`;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Voice WebSocket connected');
      setIsConnected(true);
      setConnectionState('connected');
      setError(null);
      sendClientLog('WS_CONNECTED');
      startMicrophoneCapture();
    };

    ws.onmessage = async (event) => {
      // Handle Binary TTS Audio Chunk (Int16 24kHz PCM from backend)
      if (event.data instanceof Blob) {
        if (speakingDebounceTimerRef.current) {
          clearTimeout(speakingDebounceTimerRef.current);
        }
        setIsSpeaking(true);
        if (pendingQuestionRef.current) {
          setCurrentQuestion(pendingQuestionRef.current);
          pendingQuestionRef.current = null;
        }
        sendClientLog('AUDIO_BLOB_RECEIVED', { size_bytes: event.data.size });
        const arrayBuffer = await event.data.arrayBuffer();
        const int16Array = new Int16Array(arrayBuffer);
        playAudioChunk(int16Array);
        return;
      }

      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data);
          
          if (msg.event === 'INTERRUPT') {
            console.log('Barge-in detected: interrupting AI');
            sendClientLog('BARGE_IN_TRIGGERED');
            if (speakingDebounceTimerRef.current) {
              clearTimeout(speakingDebounceTimerRef.current);
            }
            interruptPlayback();
            setIsSpeaking(false);
          } else if (msg.event === 'SPEAKING_QUESTION') {
            if (msg.question_text) setCurrentQuestion(msg.question_text);
            if (msg.turn_id !== undefined) setQuestionIndex(msg.turn_id > 0 ? msg.turn_id - 1 : 0);
          } else if (msg.event === 'LISTENING_CANDIDATE') {
            if (speakingDebounceTimerRef.current) {
              clearTimeout(speakingDebounceTimerRef.current);
            }
            setIsSpeaking(false);
          } else if (msg.event === 'PROCESSING_RESPONSE') {
            setCurrentQuestion('Processing your answer...');
          } else if (msg.event === 'AUDIO_LEVEL') {
            const vadData = JSON.parse(msg.detail);
            const vadProb = vadData.vad_prob || 0.0;
            const rms = vadData.rms || 0.0;
            const displayVal = Math.max(vadProb, Math.min(rms * 5, 1.0));
            setMicVolume(Math.min(100, Math.round(displayVal * 100)));
            if (vadData.state) setVadState(vadData.state);
          } else if (msg.event === 'EVA_RESPONDING_BRANCH') {
            if (msg.question_text) {
              pendingQuestionRef.current = msg.question_text;
            }
          } else if (msg.event === 'TURN_COMPLETE') {
            if (speakingDebounceTimerRef.current) {
              clearTimeout(speakingDebounceTimerRef.current);
            }
            setIsSpeaking(false);
          } else if (msg.event === 'QUESTION_COMPLETE' || msg.event === 'QUESTION_UPDATE') {
            if (msg.text) setCurrentQuestion(msg.text);
            if (msg.question_text) setCurrentQuestion(msg.question_text);
            if (msg.question_index !== undefined) setQuestionIndex(msg.question_index);
          } else if (msg.event === 'INTERVIEW_PAUSED') {
            setIsPaused(true);
            isPausedRef.current = true;
            if (speakingDebounceTimerRef.current) {
              clearTimeout(speakingDebounceTimerRef.current);
            }
            interruptPlayback();
          } else if (msg.event === 'INTERVIEW_RESUMED') {
            setIsPaused(false);
            isPausedRef.current = false;
          } else if (msg.event === 'INTERVIEW_RESTARTED') {
            setIsPaused(false);
            isPausedRef.current = false;
            setQuestionIndex(0);
            if (speakingDebounceTimerRef.current) {
              clearTimeout(speakingDebounceTimerRef.current);
            }
            interruptPlayback();
          } else if (msg.event === 'INTERVIEW_COMPLETE' || msg.event === 'SESSION_DONE') {
            setIsSessionDone(true);
            stopSession();
          } else if (msg.event === 'AI_START_SPEAKING') {
            setIsSpeaking(true);
          } else if (msg.event === 'AI_STOP_SPEAKING') {
            if (speakingDebounceTimerRef.current) {
              clearTimeout(speakingDebounceTimerRef.current);
            }
            setIsSpeaking(false);
          } else if (msg.event === 'ERROR') {
            console.error('Backend Error:', msg.detail);
            setError(msg.detail || 'An error occurred during the interview session');
            setConnectionState('error');
            stopSession();
          } else if (msg.event === 'CONNECTED') {
            console.log('Session initialized. Total questions:', msg.total_questions);
            if (msg.total_questions) {
              setTotalQuestions(msg.total_questions);
              setCurrentQuestion(`Session Connected! Ready for ${msg.total_questions} questions. AI is initializing...`);
            }
          }
        } catch (err) {
          console.error('Error parsing WS message:', err);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setConnectionState('error');
      sendClientLog('WS_ERROR', { error: 'WebSocket error occurred' });
    };

    ws.onclose = () => {
      if (wsRef.current && wsRef.current !== ws) {
        return; // Ignore close events from old WebSocket instances
      }
      console.log('Voice WebSocket closed');
      setIsConnected(false);
      setConnectionState('disconnected');
      // Cannot sendClientLog here since WS is already closed
      stopSession();
    };
  }, [sessionId, token, sendClientLog]);

  const startMicrophoneCapture = async () => {
    try {
      setMicPermissionDenied(false);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mediaStreamRef.current = stream;
      sendClientLog('MIC_ACCESS_GRANTED');

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000,
      });
      audioContextRef.current = audioCtx;
      setAudioState(audioCtx.state);
      
      const unlockAudio = () => {
        if (audioCtx.state === 'suspended') {
          audioCtx.resume().then(() => {
            setAudioState(audioCtx.state);
          }).catch(() => {});
        }
      };
      window.addEventListener('click', unlockAudio, { once: true });
      window.addEventListener('touchstart', unlockAudio, { once: true });
      window.addEventListener('keydown', unlockAudio, { once: true });
      
      audioCtx.onstatechange = () => {
        setAudioState(audioCtx.state);
        sendClientLog('AUDIO_CONTEXT_STATE_CHANGE', { state: audioCtx.state });
      };
      
      nextStartTimeRef.current = audioCtx.currentTime;

      // Load our custom PCM worklet
      await audioCtx.audioWorklet.addModule('/pcm-processor.js');

      const source = audioCtx.createMediaStreamSource(stream);
      sourceNodeRef.current = source;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.5;
      analyserRef.current = analyser;
      source.connect(analyser);

      // Real-time local mic volume polling at ~20fps for responsive visual feedback
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      if (volumeIntervalRef.current) clearInterval(volumeIntervalRef.current);
      volumeIntervalRef.current = setInterval(() => {
        if (!analyserRef.current || isPausedRef.current) {
          setMicVolume(0);
          return;
        }
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / (dataArray.length || 1);
        // Scale and boost sensitivity so normal speaking voice reaches 30-80%
        const volPct = Math.min(100, Math.round((avg / 90) * 100));
        setMicVolume(volPct);
      }, 50);

      const workletNode = new AudioWorkletNode(audioCtx, 'pcm-processor');
      workletNodeRef.current = workletNode;
      source.connect(workletNode);
      workletNode.connect(audioCtx.destination);

      workletNode.port.onmessage = (event) => {
        // Send Int16Array to backend over WebSocket (muted if paused)
        if (isPausedRef.current) return;
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          // Send audio regardless of isSpeaking state to allow barge-in detection
          wsRef.current.send(event.data);
        }
      };
    } catch (err) {
      console.error('Error accessing microphone:', err);
      sendClientLog('MIC_ACCESS_DENIED', { error: err.message });
      setMicPermissionDenied(true);
      setError('Microphone access denied or unavailable. Please check microphone permissions in your browser settings.');
    }
  };

  const playAudioChunk = (int16Array) => {
    if (isPausedRef.current) return;
    const audioCtx = audioContextRef.current;
    if (!audioCtx) return;

    // Convert Int16 to Float32 for Web Audio API playback
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
    }

    const audioBuffer = audioCtx.createBuffer(1, float32Array.length, 24000);
    audioBuffer.getChannelData(0).set(float32Array);

    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioCtx.destination);

    // Schedule playback seamlessly
    const currentTime = audioCtx.currentTime;
    const startTime = Math.max(currentTime, nextStartTimeRef.current);
    source.start(startTime);
    nextStartTimeRef.current = startTime + audioBuffer.duration;

    sourceNodesQueueRef.current.push(source);
    source.onended = () => {
      sourceNodesQueueRef.current = sourceNodesQueueRef.current.filter(n => n !== source);
      if (sourceNodesQueueRef.current.length === 0) {
        if (speakingDebounceTimerRef.current) {
          clearTimeout(speakingDebounceTimerRef.current);
        }
        speakingDebounceTimerRef.current = setTimeout(() => {
          if (sourceNodesQueueRef.current.length === 0) {
            setIsSpeaking(false);
          }
        }, 180);
      }
    };
  };

  const interruptPlayback = () => {
    if (speakingDebounceTimerRef.current) {
      clearTimeout(speakingDebounceTimerRef.current);
    }
    sourceNodesQueueRef.current.forEach(source => {
      try {
        source.stop();
      } catch (e) {
        // Source might already be stopped
      }
    });
    sourceNodesQueueRef.current = [];
    if (audioContextRef.current) {
      nextStartTimeRef.current = audioContextRef.current.currentTime;
    }
    setIsSpeaking(false);
  };

  const pauseInterview = useCallback(() => {
    setIsPaused(true);
    isPausedRef.current = true;
    interruptPlayback();
    sendClientLog('PAUSE_INTERVIEW');
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ action: 'pause' }));
      } catch (e) {
        console.error('Failed to send pause action:', e);
      }
    }
  }, [sendClientLog]);

  const resumeInterview = useCallback(() => {
    setIsPaused(false);
    isPausedRef.current = false;
    sendClientLog('RESUME_INTERVIEW');
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ action: 'resume' }));
      } catch (e) {
        console.error('Failed to send resume action:', e);
      }
    }
  }, [sendClientLog]);

  const restartInterview = useCallback(() => {
    setIsPaused(false);
    isPausedRef.current = false;
    interruptPlayback();
    setQuestionIndex(0);
    setCurrentQuestion('Restarting interview from beginning...');
    sendClientLog('RESTART_INTERVIEW');
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ action: 'restart' }));
      } catch (e) {
        console.error('Failed to send restart action:', e);
      }
    }
  }, [sendClientLog]);

  const resumeAudio = async () => {
    if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
      try {
        await audioContextRef.current.resume();
        setAudioState(audioContextRef.current.state);
      } catch (e) {
        console.error("Failed to resume audio:", e);
      }
    }
  };

  const stopSession = () => {
    if (volumeIntervalRef.current) {
      clearInterval(volumeIntervalRef.current);
      volumeIntervalRef.current = null;
    }
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.CONNECTING) {
        const ws = wsRef.current;
        ws.onopen = () => ws.close();
        ws.onerror = null;
        ws.onmessage = null;
      } else {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setMicVolume(0);
    interruptPlayback();
  };

  useEffect(() => {
    connectWebSocket();
    return () => {
      stopSession();
    };
  }, [connectWebSocket]);

  return {
    isConnected,
    connectionState,
    micPermissionDenied,
    isSpeaking,
    isPaused,
    currentQuestion,
    questionIndex,
    totalQuestions,
    isSessionDone,
    micVolume,
    vadState,
    audioState,
    pauseInterview,
    resumeInterview,
    restartInterview,
    resumeAudio,
    error,
    stopSession,
  };
};

export default useInterviewSession;
