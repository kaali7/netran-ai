import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Sparkles,
  Brain,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  LayoutDashboard,
  Mic,
  Cpu,
  BarChart2,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import useReports from '../hooks/useReports';

export const Processing = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const { isReady, progressMessage, error, refetch } = useReports(sessionId, 3000);

  // Rotating contextual AI processing stages for UI engagement
  const [stageIndex, setStageIndex] = useState(0);
  const contextualStages = [
    'Evaluating continuous audio waveforms & vocal pitch stability...',
    'Cross-verifying candidate responses against OpenAI Whisper logs...',
    'Scoring technical accuracy across domain architecture pillars...',
    'Analyzing hesitation markers & speech pace (Words Per Minute)...',
    'Synthesizing Eva\'s per-question feedback & executive hiring signal...',
  ];

  // Rotate stage messages every 4 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % contextualStages.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Auto-navigate to report page when analysis completes
  useEffect(() => {
    if (isReady && sessionId) {
      const timer = setTimeout(() => {
        navigate(`/report/${sessionId}`);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [isReady, navigate, sessionId]);

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8f9fa 0%, #f1f3f5 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 0 32px 0',
        fontFamily: 'var(--font-family, system-ui, sans-serif)',
      }}
    >
      {/* Top Application Header */}
      <header
        style={{
          width: '100%',
          background: 'rgba(255, 255, 255, 0.92)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          padding: '16px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: '800', fontSize: '18px', color: '#65597b' }}>
          <Sparkles size={20} />
          <span>Netran AI</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>
          <ShieldCheck size={16} style={{ color: '#16a34a' }} />
          <span>Session Completed • Multimodal Evaluation Engine</span>
        </div>
      </header>

      {/* Main Center Viewport */}
      <main
        style={{
          width: '100%',
          maxWidth: '680px',
          margin: 'auto',
          padding: '0 20px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: '100%',
            background: '#ffffff',
            borderRadius: '24px',
            padding: '48px 40px',
            boxShadow: '0 20px 50px rgba(101, 89, 123, 0.08)',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            position: 'relative',
          }}
          className="animate-entrance"
        >
          {/* Animated Central Icon Frame */}
          <div
            style={{
              position: 'relative',
              width: '100px',
              height: '100px',
              borderRadius: '50%',
              background: isReady ? '#dcfce7' : error ? '#fee2e2' : '#f5f0fb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '28px',
              transition: 'all 500ms ease',
            }}
          >
            {/* Outer Pulsing Ring */}
            {!isReady && !error && (
              <div
                style={{
                  position: 'absolute',
                  inset: '-10px',
                  borderRadius: '50%',
                  border: '2px dashed #d8b4fe',
                  animation: 'spin 12s linear infinite',
                }}
              />
            )}

            {isReady ? (
              <CheckCircle2 size={48} style={{ color: '#16a34a' }} />
            ) : error ? (
              <AlertTriangle size={48} style={{ color: '#dc2626' }} />
            ) : (
              <Brain size={44} style={{ color: '#65597b' }} />
            )}
          </div>

          {/* Heading */}
          <h1
            style={{
              fontSize: '24px',
              fontWeight: '800',
              color: '#111827',
              letterSpacing: '-0.02em',
              marginBottom: '10px',
            }}
          >
            {isReady
              ? 'Evaluation Report Complete!'
              : error
              ? 'Evaluation Encountered an Issue'
              : 'Synthesizing Multimodal Interview Report'}
          </h1>

          <p
            style={{
              fontSize: '14px',
              color: '#6b7280',
              maxWidth: '520px',
              lineHeight: '1.6',
              marginBottom: '28px',
              margin: '0 auto 28px auto',
            }}
          >
            {isReady
              ? 'Your scorecards, technical pillar ratings, vocal telemetry, and Eva\'s assessments are ready.'
              : error
              ? error
              : 'Our 3-branch evaluation engine is analyzing your audio waveform, speech speed, and technical accuracy.'}
          </p>

          {/* Progress Bar or Error Controls */}
          {!error ? (
            <div style={{ width: '100%', maxWidth: '520px' }}>
              {/* Contextual rotating step indicator */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px 16px',
                  borderRadius: '9999px',
                  background: isReady ? '#f0fdf4' : '#faf5ff',
                  border: isReady ? '1px solid #bbf7d0' : '1px solid #f3e8ff',
                  color: isReady ? '#15803d' : '#65597b',
                  fontSize: '13px',
                  fontWeight: '600',
                  marginBottom: '20px',
                  transition: 'all 300ms ease',
                }}
              >
                {isReady ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <Cpu size={16} className="animate-spin" style={{ animationDuration: '3s' }} />
                )}
                <span>{isReady ? 'Report Ready! Opening Scorecard...' : contextualStages[stageIndex]}</span>
              </div>

              {/* Progress Track */}
              <div
                style={{
                  width: '100%',
                  height: '8px',
                  background: '#f3f4f6',
                  borderRadius: '9999px',
                  overflow: 'hidden',
                  position: 'relative',
                  marginBottom: '16px',
                }}
              >
                <div
                  style={{
                    width: isReady ? '100%' : '65%',
                    height: '100%',
                    background: isReady
                      ? '#22c55e'
                      : 'linear-gradient(90deg, #65597b 0%, #9333ea 50%, #65597b 100%)',
                    borderRadius: '9999px',
                    transition: 'width 600ms ease, background 300ms ease',
                  }}
                />
              </div>

              {/* Backend Live Progress Message Pill */}
              {progressMessage && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    fontWeight: '500',
                    fontStyle: 'italic',
                  }}
                >
                  Status: {progressMessage}
                </div>
              )}
            </div>
          ) : (
            /* Error Fallback Actions */
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '12px' }}>
              <button
                onClick={() => refetch()}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 20px',
                  borderRadius: '9999px',
                  background: '#65597b',
                  color: '#ffffff',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={15} />
                <span>Retry Evaluation</span>
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 20px',
                  borderRadius: '9999px',
                  background: '#f3f4f6',
                  color: '#374151',
                  border: '1px solid #e5e7eb',
                  fontWeight: '600',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                <LayoutDashboard size={15} />
                <span>Go to Dashboard</span>
              </button>
            </div>
          )}

          {/* Feature highlights grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px',
              width: '100%',
              marginTop: '36px',
              paddingTop: '28px',
              borderTop: '1px solid #f3f4f6',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
              <Mic size={18} style={{ color: '#65597b' }} />
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#374151' }}>Audio Waveform</span>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>Hesitation & Pace</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
              <BarChart2 size={18} style={{ color: '#65597b' }} />
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#374151' }}>Domain Pillars</span>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>Technical Accuracy</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
              <Zap size={18} style={{ color: '#65597b' }} />
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#374151' }}>Eva's Assessment</span>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>Q-by-Q Breakdown</span>
            </div>
          </div>
        </div>
      </main>

      {/* Inline Keyframes for Spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Processing;
