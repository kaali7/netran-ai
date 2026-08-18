import { useState, useCallback, useRef } from 'react';
import {
  uploadResume,
  ingestJD,
  startAnalysis,
  pollAnalysisStatus,
  getQuestionPreview,
} from '../services/sessionService';

export const SETUP_PHASES = {
  IDLE: 'IDLE',
  RESUME_UPLOADING: 'RESUME_UPLOADING',
  JD_EXTRACTING: 'JD_EXTRACTING',
  READY_TO_LAUNCH: 'READY_TO_LAUNCH',
  PIPELINE_RUNNING: 'PIPELINE_RUNNING',
  COMPLETED: 'COMPLETED',
};

export default function useSetup() {
  const [sessionId, setSessionId] = useState(null);
  const [parsedResume, setParsedResume] = useState(null);
  const [parsedJD, setParsedJD] = useState(null);
  const [questionPreview, setQuestionPreview] = useState(null);
  const [phase, setPhase] = useState(SETUP_PHASES.IDLE);
  const [progressMsg, setProgressMsg] = useState('');
  const [error, setError] = useState(null);
  const [isCacheAutofilled, setIsCacheAutofilled] = useState(false);

  const pollIntervalRef = useRef(null);

  /** Clear polling timer on unmount/complete */
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  /** Helper: Check if backend session is instantly ready via Cache */
  const checkInstantCache = async (targetSessionId) => {
    try {
      const statusData = await pollAnalysisStatus(targetSessionId);
      if (String(statusData.status).toLowerCase() === 'ready') {
        const previewData = await getQuestionPreview(targetSessionId);
        setQuestionPreview(previewData);
        setPhase(SETUP_PHASES.COMPLETED);
        setIsCacheAutofilled(true);
        return true;
      }
    } catch (err) {
      // Ignore background errors during opportunistic caching check
    }
    return false;
  };

  /** 1. Upload & parse candidate resume */
  const handleResumeUpload = async (file) => {
    try {
      setError(null);
      setPhase(SETUP_PHASES.RESUME_UPLOADING);
      const data = await uploadResume(file);

      setSessionId(data.session_id);
      setParsedResume(data.parsed_resume);

      if (data.cached) {
        const isReady = await checkInstantCache(data.session_id);
        if (isReady) return data;
      }

      if (parsedJD) {
        setPhase(SETUP_PHASES.READY_TO_LAUNCH);
      } else {
        setPhase(SETUP_PHASES.IDLE);
      }
      return data;
    } catch (err) {
      console.error('Resume upload failed:', err);
      let msg = err.response?.data?.detail;
      if (!msg && (err.code === 'ECONNABORTED' || err.message?.includes('timeout'))) {
        msg = 'AI resume parsing timed out. Please click to try uploading again.';
      } else if (!msg) {
        msg = 'Failed to upload resume. Please try again.';
      }
      setError(msg);
      setPhase(SETUP_PHASES.IDLE);
      throw err;
    }
  };

  /** 2. Ingest & extract Job Description text */
  const handleJdSubmit = async (rawText, currentSessionId = sessionId) => {
    if (!rawText || rawText.trim().length < 50) {
      setError('Please paste a complete Job Description (minimum 50 characters).');
      return;
    }

    try {
      setError(null);
      setPhase(SETUP_PHASES.JD_EXTRACTING);
      const data = await ingestJD(rawText, currentSessionId);

      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }
      setParsedJD(data.parsed_jd);

      if (data.cached) {
        const isReady = await checkInstantCache(data.session_id || sessionId);
        if (isReady) return data;
      }

      if (parsedResume || data.session_id) {
        setPhase(SETUP_PHASES.READY_TO_LAUNCH);
      } else {
        setPhase(SETUP_PHASES.IDLE);
      }
      return data;
    } catch (err) {
      console.error('JD ingestion failed:', err);
      let msg = err.response?.data?.detail;
      if (!msg && (err.code === 'ECONNABORTED' || err.message?.includes('timeout'))) {
        msg = 'AI Job Description extraction timed out. Please try submitting again.';
      } else if (!msg) {
        msg = 'Failed to extract Job Description text.';
      }
      setError(msg);
      setPhase(SETUP_PHASES.IDLE);
      throw err;
    }
  };

  /** 3. Poll pipeline execution status until READY */
  const startStatusPolling = useCallback(
    (targetSessionId) => {
      stopPolling();

      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusData = await pollAnalysisStatus(targetSessionId);
          const currentStatus = String(statusData.status).toLowerCase();

          if (statusData.progress_message) {
            setProgressMsg(statusData.progress_message);
          }

          if (currentStatus === 'ready') {
            stopPolling();
            // Fetch final generated preview
            const previewData = await getQuestionPreview(targetSessionId);
            setQuestionPreview(previewData);
            setPhase(SETUP_PHASES.COMPLETED);
          } else if (currentStatus === 'failed' || currentStatus === 'error') {
            stopPolling();
            setError('Pipeline analysis encountered an error. Please try launching again.');
            setPhase(SETUP_PHASES.READY_TO_LAUNCH);
          }
        } catch (err) {
          console.error('Error polling status:', err);
        }
      }, 3000);
    },
    [stopPolling]
  );

  /** 4. Trigger Stage 1 & 2 background pipeline */
  const handleStartPipeline = async (targetSeniority = 'Senior') => {
    if (!sessionId) {
      setError('Missing active session. Please upload a resume first.');
      return;
    }
    if (!parsedJD) {
      setError('Missing Job Description. Please paste or upload a JD first.');
      return;
    }

    try {
      setError(null);
      setPhase(SETUP_PHASES.PIPELINE_RUNNING);
      setProgressMsg('Initiating market research & question tree generator...');

      await startAnalysis(sessionId, targetSeniority, true);
      startStatusPolling(sessionId);
    } catch (err) {
      console.error('Failed to start pipeline:', err);
      const msg = err.response?.data?.detail || 'Failed to start interview engine.';
      setError(msg);
      setPhase(SETUP_PHASES.READY_TO_LAUNCH);
    }
  };

  return {
    sessionId,
    parsedResume,
    parsedJD,
    questionPreview,
    phase,
    progressMsg,
    error,
    isResumeUploading: phase === SETUP_PHASES.RESUME_UPLOADING,
    isJdExtracting: phase === SETUP_PHASES.JD_EXTRACTING,
    isPipelineRunning: phase === SETUP_PHASES.PIPELINE_RUNNING,
    isCompleted: phase === SETUP_PHASES.COMPLETED,
    isCacheAutofilled,
    handleResumeUpload,
    handleJdSubmit,
    handleStartPipeline,
    stopPolling,
  };
}
