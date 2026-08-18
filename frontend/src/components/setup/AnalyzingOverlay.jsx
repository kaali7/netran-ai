import React from 'react';
import { Cpu, Loader2, CheckCircle2, Sparkles, Network } from 'lucide-react';

/**
 * AnalyzingOverlay — Full-screen glassmorphic progress modal displayed during
 * Stage 1 (Tavily research) + Stage 2 (Question Tree & Persona engine) background analysis.
 *
 * @param {boolean} isOpen - Whether overlay is visible
 * @param {string} progressMsg - Live human-readable message polled from backend
 */
export const AnalyzingOverlay = ({ isOpen, progressMsg }) => {
  if (!isOpen) return null;

  const milestones = [
    { label: 'Ingesting candidate resume & job description context', done: true },
    { label: 'Performing real-time web & tech stack research', done: true },
    { label: 'Synthesizing technical assessment rubrics', done: Boolean(progressMsg && !progressMsg.includes('Starting')) },
    { label: 'Building 15-question adaptive interview tree', done: Boolean(progressMsg && (progressMsg.includes('question') || progressMsg.includes('persona') || progressMsg.includes('completed'))) },
    { label: 'Calibrating Eva AI persona behavior & voice prompt', done: Boolean(progressMsg && progressMsg.includes('persona')) },
  ];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(15, 12, 25, 0.65)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        animation: 'fadeInOverlay 300ms cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(245, 240, 255, 0.92))',
          borderRadius: '24px',
          border: '1.5px solid rgba(255, 255, 255, 0.6)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
          padding: '36px 32px',
          textAlign: 'center',
          animation: 'slideUpModal 350ms cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Animated Icon Header */}
        <div style={{ position: 'relative', display: 'inline-block', marginBottom: '20px' }}>
          <div
            style={{
              width: '68px',
              height: '68px',
              borderRadius: '20px',
              background: 'linear-gradient(135deg, var(--primary) 0%, #3d3154 100%)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(101, 89, 123, 0.35)',
              margin: '0 auto',
            }}
          >
            <Cpu size={32} style={{ animation: 'pulse 2s ease-in-out infinite' }} />
          </div>
          <div
            style={{
              position: 'absolute',
              bottom: '-6px',
              right: '-6px',
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              background: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            }}
          >
            <Loader2 size={16} color="var(--primary)" style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        </div>

        {/* Title */}
        <h2 className="text-headline-lg" style={{ fontSize: '22px', marginBottom: '6px' }}>
          Generating Practice Track
        </h2>
        <p className="text-body-md" style={{ fontSize: '14px', color: 'var(--on-surface-variant)', marginBottom: '24px' }}>
          Eva AI is synthesizing market research and building your adaptive question tree.
        </p>

        {/* Live Status Message Card */}
        <div
          style={{
            background: 'rgba(101, 89, 123, 0.08)',
            border: '1px solid rgba(101, 89, 123, 0.15)',
            borderRadius: '14px',
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '24px',
            textAlign: 'left',
          }}
        >
          <Sparkles size={16} color="var(--primary)" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--primary)' }}>
            {progressMsg || 'Processing background pipeline...'}
          </span>
        </div>

        {/* Milestone Steps List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', textAlign: 'left' }}>
          {milestones.map((m, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                fontSize: '13px',
                color: m.done ? 'var(--on-surface)' : 'var(--outline)',
                fontWeight: m.done ? '600' : '400',
              }}
            >
              {m.done ? (
                <CheckCircle2 size={16} color="var(--secondary)" style={{ flexShrink: 0 }} />
              ) : (
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    border: '1.5px solid var(--outline-variant)',
                    flexShrink: 0,
                  }}
                />
              )}
              <span>{m.label}</span>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes fadeInOverlay {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUpModal {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.08); opacity: 0.85; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AnalyzingOverlay;
