import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AvatarEva from '../components/interview/AvatarEva';
import useInterviewSession from '../hooks/useInterviewSession';
import { triggerReportGeneration } from '../services/reportService';
import {
  Sparkles,
  Volume2,
  Mic,
  Square,
  Clock,
  ArrowLeft,
  RotateCcw,
  Pause,
  Play,
  FileText,
} from 'lucide-react';

export const Interview = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();

  // Real WebSocket Session Hook
  const { isConnected, isSpeaking, currentQuestion, isSessionDone, micVolume, stopSession } = useInterviewSession(sessionId);

  // Timer & UI State
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-navigate when session naturally ends
  useEffect(() => {
    if (isSessionDone && sessionId) {
      triggerReportGeneration(sessionId).catch((err) => console.error('Report gen trigger error:', err));
      navigate(`/processing/${sessionId}`);
    }
  }, [isSessionDone, navigate, sessionId]);

  // Timer effect starts only when connected
  useEffect(() => {
    if (!isConnected || isPaused) return;
    const interval = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
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

  const handleRestart = () => {
    setSecondsElapsed(0);
  };

  const handleTogglePause = () => {
    setIsPaused((prev) => !prev);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 0 24px 0',
        fontFamily: 'var(--font-family)',
      }}
    >
      {/* Top Application Header Bar */}
      <header
        style={{
          width: '100%',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          padding: '14px 28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)',
        }}
      >
        {/* Left Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => navigate('/setup')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--on-surface-variant)',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            <ArrowLeft size={16} />
            <span>Exit</span>
          </button>
          <div style={{ height: '18px', width: '1px', background: '#e5e7eb' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '800', fontSize: '18px', color: 'var(--primary)' }}>
            <Sparkles size={20} />
            <span>Netran AI</span>
          </div>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', background: '#ede6f8', color: 'var(--primary)', borderRadius: '9999px' }}>
            Live AI Mock Interview Room
          </span>
        </div>

        {/* Right Header Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {/* Timer Display */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--on-surface)', fontWeight: '700', fontSize: '15px' }}>
            <Clock size={16} style={{ color: 'var(--primary)' }} />
            <span>{formatTime(secondsElapsed)}</span>
          </div>

          {/* User Profile Initials */}
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'var(--primary-container)',
              color: 'var(--on-primary-container)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: '700',
              fontSize: '13px',
            }}
          >
            AS
          </div>
        </div>
      </header>

      {/* Main Room Viewport Container */}
      <main
        style={{
          width: '100%',
          maxWidth: '920px',
          margin: '24px auto',
          padding: '0 20px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          flex: 1,
          justifyContent: 'center',
        }}
      >
        {/* Central Large White Card */}
        <div
          style={{
            width: '100%',
            background: '#ffffff',
            borderRadius: '24px',
            padding: '40px 48px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            position: 'relative',
          }}
          className="animate-entrance"
        >
          {/* Avatar Viewport Frame */}
          <div style={{ marginBottom: '20px' }}>
            <AvatarEva isSpeaking={isSpeaking} />
          </div>

          {/* VAD Status Pill */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 18px',
              borderRadius: '9999px',
              background: isSpeaking ? '#dcfce7' : '#f3e8ff',
              color: isSpeaking ? '#15803d' : '#6b21a8',
              border: isSpeaking ? '1px solid #bbf7d0' : '1px solid #e9d5ff',
              fontWeight: '700',
              fontSize: '13px',
              marginBottom: '28px',
              transition: 'all 300ms ease',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
            }}
          >
            {isSpeaking ? (
              <>
                <Volume2 size={16} />
                <span>VAD Status: AI Speaking</span>
              </>
            ) : (
              <>
                <Mic size={16} />
                <span>VAD Status: Candidate Turn (Listening)</span>
              </>
            )}
          </div>

          {/* Mic Volume Level Bar */}
          {!isSpeaking && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '20px',
                background: '#f9fafb',
                padding: '6px 14px',
                borderRadius: '12px',
                border: '1px solid #e5e7eb',
              }}
            >
              <Mic size={14} style={{ color: micVolume > 5 ? '#22c55e' : '#9ca3af' }} />
              <span style={{ fontSize: '12px', fontWeight: '600', color: '#4b5563' }}>Mic Input Level:</span>
              <div
                style={{
                  width: '120px',
                  height: '8px',
                  background: '#e5e7eb',
                  borderRadius: '9999px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${micVolume}%`,
                    height: '100%',
                    background: micVolume > 40 ? '#ef4444' : micVolume > 15 ? '#22c55e' : '#3b82f6',
                    borderRadius: '9999px',
                    transition: 'width 100ms ease-out, background 200ms ease',
                  }}
                />
              </div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#6b7280', minWidth: '28px' }}>
                {micVolume}%
              </span>
            </div>
          )}

          {/* Interview Question Text */}
          <h2
            style={{
              fontSize: '22px',
              fontWeight: '700',
              lineHeight: '34px',
              color: '#1f2937',
              maxWidth: '720px',
              marginBottom: '32px',
              letterSpacing: '-0.01em',
            }}
          >
            {currentQuestion}
          </h2>
        </div>
      </main>

      {/* Floating Bottom Control Bar */}
      <footer style={{ marginBottom: '12px' }}>
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.92)',
            backdropFilter: 'blur(16px)',
            borderRadius: '9999px',
            padding: '10px 28px',
            boxShadow: '0 12px 36px rgba(0, 0, 0, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.8)',
            display: 'flex',
            alignItems: 'center',
            gap: '32px',
          }}
          className="animate-entrance animate-delay-1"
        >
          {/* Restart Button */}
          <button
            onClick={handleRestart}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              color: '#4b5563',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: '#f3f4f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <RotateCcw size={17} />
            </div>
            <span style={{ fontSize: '11px', fontWeight: '700' }}>Restart</span>
          </button>

          {/* Pause / Resume Button */}
          <button
            onClick={handleTogglePause}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              color: '#4b5563',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: isPaused ? '#fef3c7' : '#f3f4f6',
                color: isPaused ? '#d97706' : '#4b5563',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isPaused ? <Play size={17} /> : <Pause size={17} />}
            </div>
            <span style={{ fontSize: '11px', fontWeight: '700' }}>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          {/* Stop Session Button */}
          <button
            onClick={handleStopSession}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              color: 'var(--primary)',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'var(--primary-container)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--on-primary-container)',
              }}
            >
              <FileText size={16} />
            </div>
            <span style={{ fontSize: '11px', fontWeight: '700' }}>End & Get Feedback</span>
          </button>
        </div>
      </footer>
    </div>
  );
};

export default Interview;
