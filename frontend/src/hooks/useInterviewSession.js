import { useState, useEffect, useRef, useCallback } from 'react';
import useAuth from './useAuth';

export const useInterviewSession = (sessionId) => {
  const { token } = useAuth();
  
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('connecting'); // 'connecting' | 'connected' | 'disconnected' | 'error'
  const [micPermissionDenied, setMicPermissionDenied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('Initializing interview session...');
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(15);
  const [isSessionDone, setIsSessionDone] = useState(false);
  const [micVolume, setMicVolume] = useState(0);
  const [vadState, setVadState] = useState('Mic: Offline');
  const [audioState, setAudioState] = useState('suspended');
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const workletNodeRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const analyserRef = useRef(null);
  const volumeIntervalRef = useRef(null);
  
  // TTS Playback state
  const nextStartTimeRef = useRef(0);
  const sourceNodesQueueRef = useRef([]);

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
      // Handle Binary TTS Audio Chunk (assuming Int16 16kHz PCM from backend)
      if (event.data instanceof Blob) {
        setIsSpeaking(true);
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
            interruptPlayback();
            setIsSpeaking(false);
          } else if (msg.event === 'SPEAKING_QUESTION') {
            setIsSpeaking(true);
            if (msg.question_text) setCurrentQuestion(msg.question_text);
            if (msg.turn_id !== undefined) setQuestionIndex(msg.turn_id > 0 ? msg.turn_id - 1 : 0);
          } else if (msg.event === 'LISTENING_CANDIDATE') {
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
            setIsSpeaking(true);
            if (msg.question_text) setCurrentQuestion(msg.question_text);
          } else if (msg.event === 'TURN_COMPLETE') {
            setIsSpeaking(false);
          } else if (msg.event === 'QUESTION_COMPLETE' || msg.event === 'QUESTION_UPDATE') {
            if (msg.text) setCurrentQuestion(msg.text);
            if (msg.question_text) setCurrentQuestion(msg.question_text); // some backend events use question_text
            if (msg.question_index !== undefined) setQuestionIndex(msg.question_index);
          } else if (msg.event === 'INTERVIEW_COMPLETE' || msg.event === 'SESSION_DONE') {
            setIsSessionDone(true);
            stopSession();
          } else if (msg.event === 'AI_START_SPEAKING') {
            setIsSpeaking(true);
          } else if (msg.event === 'AI_STOP_SPEAKING') {
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
      analyserRef.current = analyser;
      source.connect(analyser);

      const workletNode = new AudioWorkletNode(audioCtx, 'pcm-processor');
      workletNodeRef.current = workletNode;
      source.connect(workletNode);
      workletNode.connect(audioCtx.destination);

      workletNode.port.onmessage = (event) => {
        // Send Int16Array to backend over WebSocket
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
        setIsSpeaking(false);
      }
    };
  };

  const interruptPlayback = () => {
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
    currentQuestion,
    questionIndex,
    totalQuestions,
    isSessionDone,
    micVolume,
    vadState,
    audioState,
    resumeAudio,
    error,
    stopSession,
  };
};

export default useInterviewSession;
