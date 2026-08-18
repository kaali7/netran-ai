import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AvatarEva from '../components/interview/AvatarEva';
import {
  Sparkles,
  Volume2,
  Mic,
  RotateCcw,
  Pause,
  Play,
  Square,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Star,
  Settings,
  User,
  ArrowLeft,
  VolumeX,
} from 'lucide-react';

export const Interview = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();

  // State management
  const [isSpeaking, setIsSpeaking] = useState(true); // AI speaking vs candidate turn
  const [isPaused, setIsPaused] = useState(false);
  const [secondsElapsed, setSecondsElapsed] = useState(252); // Starts at 04:12 for fidelity
  const [questionIndex, setQuestionIndex] = useState(0);

  const questions = [
    'How would you handle cache invalidation in a multi-region Redis cluster when consistency is critical for user balances?',
    'Can you explain how you would design a rate limiter middleware for a high-throughput API gateway?',
    'What strategies do you employ to prevent race conditions when handling simultaneous DB writes in Node.js?',
  ];

  // Timer effect
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isPaused]);

  // Format seconds to mm:ss
  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleToggleVAD = () => {
    setIsSpeaking((prev) => !prev);
  };

  const handleRestart = () => {
    setSecondsElapsed(0);
    setIsSpeaking(true);
  };

  const handleTogglePause = () => {
    setIsPaused((prev) => !prev);
  };

  const handleStopSession = () => {
    navigate(`/report/${sessionId || 'sess_demo123'}`);
  };

  const handleNextQuestion = () => {
    setQuestionIndex((prev) => (prev + 1) % questions.length);
    setIsSpeaking(true);
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

          {/* Feedback & Settings */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#6b7280' }}>
            <button title="Bookmark" style={{ cursor: 'pointer', color: 'inherit' }}>
              <Star size={18} />
            </button>
            <button title="Good Response" style={{ cursor: 'pointer', color: 'inherit' }}>
              <ThumbsUp size={18} />
            </button>
            <button title="Needs Improvement" style={{ cursor: 'pointer', color: 'inherit' }}>
              <ThumbsDown size={18} />
            </button>
            <button title="Settings" style={{ cursor: 'pointer', color: 'inherit' }}>
              <Settings size={18} />
            </button>
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
          <div
            onClick={handleToggleVAD}
            title="Click avatar to toggle AI Speaking / Listening turn"
            style={{ cursor: 'pointer', marginBottom: '20px' }}
          >
            <AvatarEva isSpeaking={isSpeaking && !isPaused} />
          </div>

          {/* VAD Status Pill */}
          <div
            onClick={handleToggleVAD}
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
              cursor: 'pointer',
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
            {questions[questionIndex]}
          </h2>

          {/* Replay / Next Question Action */}
          <button
            onClick={handleNextQuestion}
            className="btn btn-ghost"
            style={{
              borderRadius: '9999px',
              padding: '10px 22px',
              fontSize: '14px',
              color: '#4b5563',
              border: '1.5px solid #e5e7eb',
              gap: '8px',
            }}
          >
            <RotateCcw size={15} />
            <span>Replay Question</span>
          </button>
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
              color: '#dc2626',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: '#fee2e2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#dc2626',
              }}
            >
              <Square size={16} fill="#dc2626" />
            </div>
            <span style={{ fontSize: '11px', fontWeight: '700' }}>Stop</span>
          </button>
        </div>
      </footer>
    </div>
  );
};

export default Interview;
