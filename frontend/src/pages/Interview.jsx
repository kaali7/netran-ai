import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AvatarEva from '../components/interview/AvatarEva';
import useInterviewSession from '../hooks/useInterviewSession';
import useAuth from '../hooks/useAuth';
import { triggerReportGeneration } from '../services/reportService';
import {
  Sparkles,
  Volume2,
  Mic,
  Clock,
  Timer,
  ArrowLeft,
  RotateCcw,
  Pause,
  Play,
  FileText,
  AlertCircle,
  XCircle,
} from 'lucide-react';

export const Interview = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const { user } = useAuth();
  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : 'C';

  // Real WebSocket Session Hook
  const {
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
  } = useInterviewSession(sessionId);

  // Timer & UI State
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [questionSecondsElapsed, setQuestionSecondsElapsed] = useState(0);
  const [showRestartModal, setShowRestartModal] = useState(false);

  // Auto-navigate when session naturally ends
  useEffect(() => {
    if (isSessionDone && sessionId) {
      triggerReportGeneration(sessionId).catch((err) => console.error('Report gen trigger error:', err));
      navigate(`/processing/${sessionId}`);
    }
  }, [isSessionDone, navigate, sessionId]);

  // Reset per-question timer whenever questionIndex changes
  useEffect(() => {
    setQuestionSecondsElapsed(0);
  }, [questionIndex]);

  // Timer effect starts only when connected and not paused
  useEffect(() => {
    if (!isConnected || isPaused) return;
    const interval = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
      setQuestionSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isConnected, isPaused]);

  // Format seconds to mm:ss
  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStopSession = () => {
    stopSession();
    if (sessionId) {
      triggerReportGeneration(sessionId).catch((err) => console.error('Report gen trigger error:', err));
      navigate(`/processing/${sessionId}`);
    } else {
      navigate('/dashboard');
    }
  };

  const handleAbortSession = () => {
    stopSession();
    navigate('/dashboard');
  };

  const handleRestartConfirm = () => {
    setShowRestartModal(false);
    setSecondsElapsed(0);
    setQuestionSecondsElapsed(0);
    restartInterview();
  };

  const handleTogglePause = () => {
    if (isPaused) {
      resumeInterview();
    } else {
      pauseInterview();
    }
  };

  return (
    <div className="interview-page-container">
      {/* Scoped CSS for Single Screen Mobile Viewport */}
      <style>{`
        .interview-page-container {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          width: 100vw;
          height: 100dvh;
          max-height: 100dvh;
          overflow: hidden;
          background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          padding: 0;
          margin: 0;
          font-family: var(--font-family, 'Manrope', sans-serif);
          box-sizing: border-box;
          z-index: 100;
        }

        /* Top Header */
        .interview-header {
          width: 100%;
          height: 56px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-bottom: 1px solid rgba(0, 0, 0, 0.07);
          padding: 0 16px;
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          align-items: center;
          box-sizing: border-box;
          flex-shrink: 0;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
        }

        .interview-header-left {
          display: flex;
          align-items: center;
          gap: 10px;
          justify-self: start;
        }

        .interview-exit-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: var(--on-surface-variant, #49454d);
          font-size: 13px;
          font-weight: 700;
          cursor: pointer;
          background: #f3f4f6;
          border: 1px solid #e5e7eb;
          padding: 6px 12px;
          border-radius: 9999px;
          transition: all 150ms ease;
        }

        .interview-exit-btn:hover {
          background: #e5e7eb;
          color: var(--on-surface, #191c1d);
        }

        .interview-brand {
          display: flex;
          align-items: center;
          gap: 6px;
          font-weight: 800;
          font-size: 16px;
          color: var(--primary, #65597b);
        }

        .interview-header-center {
          display: flex;
          align-items: center;
          justify-content: center;
          justify-self: center;
        }

        .interview-q-pill {
          font-size: 12px;
          font-weight: 700;
          padding: 5px 14px;
          background: #ede6f8;
          color: var(--primary, #65597b);
          border: 1px solid rgba(101, 89, 123, 0.15);
          border-radius: 9999px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          white-space: nowrap;
          box-shadow: 0 1px 4px rgba(101, 89, 123, 0.06);
        }

        .interview-header-right {
          display: flex;
          align-items: center;
          gap: 8px;
          justify-self: end;
        }

        .interview-user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: var(--primary-container, #e6d6ff);
          color: var(--on-primary-container, #4d4162);
          border: 1.5px solid rgba(101, 89, 123, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 13px;
          flex-shrink: 0;
        }

        /* Main Center Viewport */
        .interview-main {
          width: 100%;
          max-width: 920px;
          flex: 1;
          min-height: 0;
          margin: 0 auto;
          padding: 16px 16px 10px 16px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          box-sizing: border-box;
          overflow: hidden;
        }

        /* Central Card */
        .interview-card {
          width: 100%;
          height: 100%;
          max-height: 100%;
          background: #ffffff;
          border-radius: 22px;
          padding: 18px 20px 16px 20px;
          box-shadow: 0 12px 36px rgba(0, 0, 0, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.85);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          text-align: center;
          position: relative;
          box-sizing: border-box;
          overflow: hidden;
        }

        /* Avatar Container - Snug 1:1 Aspect Ratio Matching Character Frame */
        .interview-avatar-wrapper {
          width: clamp(190px, 29vh, 240px);
          height: clamp(190px, 29vh, 240px);
          aspect-ratio: 1 / 1;
          border-radius: 22px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          margin-bottom: 8px;
          position: relative;
          background: #ffffff;
          box-shadow: 0 8px 24px rgba(101, 89, 123, 0.1);
          border: 2px solid rgba(101, 89, 123, 0.12);
          transition: transform 200ms ease, box-shadow 200ms ease;
          overflow: hidden;
        }

        .interview-avatar-speaking {
          border-color: #86efac;
          box-shadow: 0 0 0 3px #bbf7d0, 0 12px 32px rgba(34, 197, 94, 0.25);
        }

        /* VAD Status Pill */
        .interview-vad-pill {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 5px 16px;
          border-radius: 9999px;
          font-weight: 700;
          font-size: 12px;
          margin-bottom: 6px;
          transition: background 250ms ease, color 250ms ease, border-color 250ms ease;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
          min-height: 28px;
          min-width: 150px;
          box-sizing: border-box;
          flex-shrink: 0;
        }

        /* Telemetry Row */
        .interview-telemetry-row {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 6px;
          flex-shrink: 0;
        }

        /* Mic Level Row */
        .interview-mic-row {
          display: flex;
          align-items: center;
          gap: 6px;
          background: #f9fafb;
          padding: 4px 12px;
          border-radius: 10px;
          border: 1px solid #e5e7eb;
          min-height: 26px;
          box-sizing: border-box;
          flex-shrink: 0;
        }

        .interview-mic-bar-track {
          width: 80px;
          height: 6px;
          background: #e5e7eb;
          border-radius: 9999px;
          overflow: hidden;
        }

        /* Question Pacing Badge */
        .interview-pacing-badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-size: 11px;
          font-weight: 600;
          color: #4b5563;
          background: #f9fafb;
          padding: 4px 10px;
          border-radius: 10px;
          border: 1px solid #e5e7eb;
          min-height: 26px;
          box-sizing: border-box;
          flex-shrink: 0;
        }

        /* Question Text Container */
        .interview-question-scroll-box {
          flex: 1;
          min-height: 0;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow-y: auto;
          padding: 6px 10px;
          box-sizing: border-box;
          scrollbar-width: thin;
        }

        .interview-question-text {
          font-size: clamp(15px, 2.3vh, 19px);
          font-weight: 700;
          line-height: 1.45;
          color: #1f2937;
          max-width: 720px;
          margin: 0;
          letter-spacing: -0.01em;
        }

        /* Footer Control Bar */
        .interview-footer {
          width: 100%;
          padding: 4px 16px max(10px, env(safe-area-inset-bottom, 10px));
          display: flex;
          justify-content: center;
          flex-shrink: 0;
          box-sizing: border-box;
        }

        .interview-controls-pill {
          background: rgba(255, 255, 255, 0.94);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-radius: 9999px;
          padding: 6px 18px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.9);
          display: flex;
          align-items: center;
          justify-content: space-around;
          gap: 16px;
          width: 100%;
          max-width: 480px;
          box-sizing: border-box;
        }

        .interview-ctrl-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          cursor: pointer;
          border: none;
          background: transparent;
          padding: 2px 4px;
          transition: transform 120ms ease;
        }

        .interview-ctrl-btn:active {
          transform: scale(0.95);
        }

        .interview-ctrl-icon {
          width: 34px;
          height: 34px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 150ms;
        }

        .interview-ctrl-label {
          font-size: 10px;
          font-weight: 700;
          white-space: nowrap;
        }

        /* Responsive Mobile Specific Queries */
        @media (max-width: 640px) {
          .interview-header {
            height: 50px;
            padding: 0 12px;
          }
          .interview-exit-btn {
            padding: 4px 10px;
            font-size: 12px;
          }
          .interview-brand {
            display: none;
          }
          .interview-header-left {
            gap: 0;
          }
          .interview-q-pill {
            font-size: 11px;
            padding: 4px 10px;
          }
          .interview-user-avatar {
            width: 28px;
            height: 28px;
            font-size: 12px;
          }
          .interview-main {
            padding: 12px 12px 8px 12px;
          }
          .interview-card {
            padding: 16px 14px 12px 14px;
            border-radius: 20px;
          }
          .interview-avatar-wrapper {
            width: clamp(170px, 27vh, 205px);
            height: clamp(170px, 27vh, 205px);
            aspect-ratio: 1 / 1;
            border-radius: 20px;
            margin-top: 2px;
            margin-bottom: 6px;
          }
          .interview-vad-pill {
            font-size: 11px;
            padding: 4px 12px;
            min-height: 26px;
            min-width: 135px;
            margin-bottom: 4px;
          }
          .interview-telemetry-row {
            gap: 6px;
            margin-bottom: 4px;
          }
          .interview-mic-row {
            padding: 2px 8px;
            min-height: 22px;
            gap: 4px;
          }
          .interview-mic-bar-track {
            width: 55px;
            height: 5px;
          }
          .interview-pacing-badge {
            font-size: 10px;
            padding: 2px 8px;
            min-height: 22px;
          }
          .interview-question-text {
            font-size: 15px;
            line-height: 1.4;
          }
          .interview-controls-pill {
            padding: 4px 12px;
            gap: 8px;
          }
          .interview-ctrl-icon {
            width: 30px;
            height: 30px;
          }
          .interview-ctrl-label {
            font-size: 9px;
          }
        }

        @media (min-width: 769px) {
          .interview-avatar-wrapper {
            width: 320px;
            height: 260px;
            margin-bottom: 16px;
          }
          .interview-card {
            padding: 32px 40px;
          }
          .interview-question-text {
            font-size: 21px;
            line-height: 32px;
          }
        }
      `}</style>

      {/* Top Application Header Bar */}
      <header className="interview-header">
        {/* Left: Exit & Branding */}
        <div className="interview-header-left">
          <button
            onClick={() => navigate('/setup')}
            className="interview-exit-btn"
            title="Exit to Setup"
          >
            <ArrowLeft size={15} />
            <span>Exit</span>
          </button>
          <div className="interview-brand" style={{ marginLeft: '6px' }}>
            <Sparkles size={16} />
            <span>Netran AI</span>
          </div>
        </div>

        {/* Center: Question Progress Pill */}
        <div className="interview-header-center">
          <div className="interview-q-pill">
            <Sparkles size={12} />
            <span>Question {questionIndex + 1} of {totalQuestions || 15}</span>
          </div>
        </div>

        {/* Right: Candidate Avatar Initial */}
        <div className="interview-header-right">
          <div className="interview-user-avatar" title={`Signed in as ${user?.email || 'Candidate'}`}>
            {userInitial}
          </div>
        </div>
      </header>

      {/* Main Room Viewport Container */}
      <main className="interview-main">
        {/* Mic Permission Denied Alert Banner */}
        {micPermissionDenied && (
          <div
            style={{
              width: '100%',
              marginBottom: '10px',
              padding: '10px 14px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              color: '#991b1b',
              fontSize: '12px',
              fontWeight: '600',
              boxShadow: '0 2px 8px rgba(239, 68, 68, 0.06)',
              flexShrink: 0,
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, color: '#dc2626' }} />
            <div>
              <strong>Microphone Access Denied: </strong>
              <span>Please allow microphone access in your browser settings and refresh.</span>
            </div>
          </div>
        )}

        {/* Error Notification Banner if present */}
        {error && !micPermissionDenied && (
          <div
            style={{
              width: '100%',
              marginBottom: '10px',
              padding: '10px 14px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              color: '#991b1b',
              fontSize: '12px',
              fontWeight: '600',
              boxShadow: '0 2px 8px rgba(239, 68, 68, 0.06)',
              flexShrink: 0,
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Central Card */}
        <div className="interview-card animate-entrance">
          {/* Connection Loading Overlay */}
          {connectionState === 'connecting' && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                background: 'rgba(255, 255, 255, 0.94)',
                backdropFilter: 'blur(8px)',
                borderRadius: '20px',
                zIndex: 10,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
              }}
            >
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  border: '3px solid #ede6f8',
                  borderTopColor: '#65597b',
                  animation: 'spin 1s linear infinite',
                  marginBottom: '12px',
                }}
              />
              <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#111827', margin: '0 0 4px 0' }}>
                Connecting to Eva's Voice Engine...
              </h3>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                Establishing real-time full-duplex WebSocket stream
              </p>
            </div>
          )}

          {/* Autoplay Suspended Overlay */}
          {audioState === 'suspended' && connectionState === 'connected' && !micPermissionDenied && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                background: 'rgba(255, 255, 255, 0.96)',
                backdropFilter: 'blur(8px)',
                borderRadius: '20px',
                zIndex: 10,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
              }}
            >
              <button
                onClick={resumeAudio}
                style={{
                  background: 'var(--primary, #65597b)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '9999px',
                  fontSize: '14px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: '0 8px 24px rgba(101, 89, 123, 0.25)',
                }}
              >
                <Volume2 size={20} />
                <span>Tap to Enable Audio & Join</span>
              </button>
              <p style={{ marginTop: '10px', fontSize: '12px', color: '#4b5563', maxWidth: '320px', textAlign: 'center' }}>
                Browser audio requires a user interaction to start speaker output.
              </p>
            </div>
          )}

          {/* Top Half: Avatar and Indicators */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0, width: '100%' }}>
            {/* Avatar Viewport Frame */}
            <div className={`interview-avatar-wrapper ${isSpeaking ? 'interview-avatar-speaking' : ''}`}>
              <AvatarEva isSpeaking={isSpeaking} />
            </div>

            {/* VAD Status Pill */}
            <div
              className="interview-vad-pill"
              style={{
                background: isPaused ? '#fef3c7' : isSpeaking ? '#dcfce7' : '#f3e8ff',
                color: isPaused ? '#d97706' : isSpeaking ? '#15803d' : '#6b21a8',
                border: isPaused ? '1px solid #fde68a' : isSpeaking ? '1px solid #bbf7d0' : '1px solid #e9d5ff',
              }}
            >
              {isPaused ? (
                <>
                  <Pause size={14} style={{ flexShrink: 0 }} />
                  <span>Interview Paused</span>
                </>
              ) : isSpeaking ? (
                <>
                  <Volume2 size={14} style={{ flexShrink: 0 }} />
                  <span>Eva is Speaking</span>
                </>
              ) : (
                <>
                  <Mic size={14} style={{ flexShrink: 0 }} />
                  <span>
                    {(() => {
                      if (!vadState) return 'Listening...';
                      const lower = vadState.toLowerCase();
                      if (lower.includes('hearing')) return 'Hearing you...';
                      if (lower.includes('processing') || lower.includes('transcription')) return 'Processing answer...';
                      if (lower.includes('standby') || lower.includes('offline')) return 'Mic: Standby';
                      return 'Listening...';
                    })()}
                  </span>
                </>
              )}
            </div>

            {/* Telemetry Row: Mic Level & Pacing Timer */}
            <div className="interview-telemetry-row">
              {/* Mic Volume Level Bar */}
              <div
                className="interview-mic-row"
                style={{
                  opacity: isSpeaking || isPaused ? 0.45 : 1,
                  pointerEvents: isSpeaking || isPaused ? 'none' : 'auto',
                  transition: 'opacity 200ms ease',
                }}
              >
                <Mic size={12} style={{ color: !isSpeaking && !isPaused && micVolume > 5 ? '#22c55e' : '#9ca3af' }} />
                <span style={{ fontSize: '11px', fontWeight: '600', color: isSpeaking || isPaused ? '#9ca3af' : '#4b5563' }}>
                  {isPaused ? 'Mic Muted (Paused)' : isSpeaking ? 'AI Output Active' : 'Mic Input:'}
                </span>
                <div className="interview-mic-bar-track">
                  <div
                    style={{
                      width: isSpeaking || isPaused ? '0%' : `${micVolume}%`,
                      height: '100%',
                      background: micVolume > 40 ? '#ef4444' : micVolume > 15 ? '#22c55e' : '#3b82f6',
                      borderRadius: '9999px',
                      transition: 'width 100ms ease-out, background 200ms ease',
                    }}
                  />
                </div>
                <span style={{ fontSize: '10px', fontWeight: '700', color: isSpeaking || isPaused ? '#9ca3af' : '#6b7280', minWidth: '24px' }}>
                  {isSpeaking || isPaused ? '—' : `${micVolume}%`}
                </span>
              </div>

              {/* Per-Question Pacing Helper Badge */}
              <div className="interview-pacing-badge">
                <Timer size={12} style={{ color: isPaused ? '#d97706' : '#16a34a' }} />
                <span>Q{questionIndex + 1}: <strong style={{ color: '#111827' }}>{formatTime(questionSecondsElapsed)}</strong></span>
                <span style={{ color: '#d1d5db' }}>•</span>
                <span style={{ color: '#6b7280' }}>Target: ~2-3m</span>
              </div>
            </div>
          </div>

          {/* Bottom Half: Question Text Scrollable Centerpiece */}
          <div className="interview-question-scroll-box">
            <h2 className="interview-question-text">
              {currentQuestion || "Preparing your customized interview question..."}
            </h2>
          </div>

          {/* Semi-Transparent Paused State Overlay */}
          {isPaused && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(255, 255, 255, 0.90)',
                backdropFilter: 'blur(8px)',
                borderRadius: '22px',
                zIndex: 8,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                textAlign: 'center',
              }}
              className="animate-entrance"
            >
              <div
                style={{
                  width: '46px',
                  height: '46px',
                  borderRadius: '50%',
                  background: '#fef3c7',
                  color: '#d97706',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '10px',
                  boxShadow: '0 4px 14px rgba(217, 119, 6, 0.15)',
                }}
              >
                <Pause size={22} />
              </div>
              <h3 style={{ fontSize: '17px', fontWeight: '800', color: '#111827', margin: '0 0 6px 0' }}>
                Interview Paused
              </h3>
              <p style={{ fontSize: '12.5px', color: '#6b7280', margin: '0 0 16px 0', maxWidth: '280px', lineHeight: '1.45' }}>
                Listening, timers, and AI voice are paused. Tap Resume to continue.
              </p>
              <button
                onClick={handleTogglePause}
                style={{
                  background: 'var(--primary, #65597b)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '10px 24px',
                  borderRadius: '9999px',
                  fontSize: '13px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 14px rgba(101, 89, 123, 0.25)',
                }}
              >
                <Play size={15} />
                <span>Resume Interview</span>
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Floating Bottom Control Bar */}
      <footer className="interview-footer">
        <div className="interview-controls-pill animate-entrance animate-delay-1">
          {/* Restart Interview Button */}
          <button
            onClick={() => setShowRestartModal(true)}
            title="Restart interview from the beginning"
            className="interview-ctrl-btn"
            style={{ color: '#4b5563' }}
          >
            <div className="interview-ctrl-icon" style={{ background: '#f3f4f6' }}>
              <RotateCcw size={15} />
            </div>
            <span className="interview-ctrl-label">Restart</span>
          </button>

          {/* Pause / Resume Button */}
          <button
            onClick={handleTogglePause}
            className="interview-ctrl-btn"
            style={{ color: isPaused ? '#d97706' : '#4b5563' }}
          >
            <div
              className="interview-ctrl-icon"
              style={{
                background: isPaused ? '#fef3c7' : '#f3f4f6',
                color: isPaused ? '#d97706' : '#4b5563',
              }}
            >
              {isPaused ? <Play size={15} /> : <Pause size={15} />}
            </div>
            <span className="interview-ctrl-label">{isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          {/* Stop Session Button */}
          <button
            onClick={handleStopSession}
            className="interview-ctrl-btn"
            style={{ color: 'var(--primary, #65597b)' }}
          >
            <div
              className="interview-ctrl-icon"
              style={{
                background: 'var(--primary-container, #e6d6ff)',
                color: 'var(--on-primary-container, #4d4162)',
              }}
            >
              <FileText size={15} />
            </div>
            <span className="interview-ctrl-label">End & Report</span>
          </button>

          {/* Abort Session Button */}
          <button
            onClick={handleAbortSession}
            className="interview-ctrl-btn"
            style={{ color: '#ef4444' }}
          >
            <div
              className="interview-ctrl-icon"
              style={{
                background: '#fee2e2',
                color: '#b91c1c',
              }}
            >
              <XCircle size={15} />
            </div>
            <span className="interview-ctrl-label">Abort</span>
          </button>
        </div>
      </footer>

      {/* Restart Interview Confirmation Modal */}
      {showRestartModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.45)',
            backdropFilter: 'blur(6px)',
            zIndex: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '24px',
              padding: '24px 28px',
              maxWidth: '380px',
              width: '100%',
              textAlign: 'center',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.15)',
              border: '1px solid rgba(255, 255, 255, 0.8)',
            }}
            className="animate-entrance"
          >
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '50%',
                background: '#ede6f8',
                color: 'var(--primary, #65597b)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 12px auto',
              }}
            >
              <RotateCcw size={22} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: '0 0 8px 0' }}>
              Restart Interview?
            </h3>
            <p style={{ fontSize: '13px', color: '#4b5563', lineHeight: '1.45', margin: '0 0 20px 0' }}>
              This will reset all questions back to the beginning and restart Eva's opening greeting.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                onClick={() => setShowRestartModal(false)}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '9999px',
                  border: '1.5px solid #e5e7eb',
                  background: '#ffffff',
                  color: '#374151',
                  fontSize: '13px',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleRestartConfirm}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '9999px',
                  border: 'none',
                  background: 'var(--primary, #65597b)',
                  color: '#ffffff',
                  fontSize: '13px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(101, 89, 123, 0.25)',
                }}
              >
                Restart
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Interview;
