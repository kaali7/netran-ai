import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Mic, ChevronRight, Loader2, AlertCircle, Zap, Server, Palette, Bot, User, Edit3 } from 'lucide-react';
import { fetchTemplates, startTemplateSession } from '../../services/templateService';
import useAuth from '../../hooks/useAuth';

/** Helper to render Lucide vector icon based on template ID */
const renderTemplateIcon = (templateId, color) => {
  if (templateId === 'backend') return <Server size={24} color={color} />;
  if (templateId === 'frontend') return <Palette size={24} color={color} />;
  return <Bot size={24} color={color} />;
};

/**
 * TemplatePicker — Glassmorphic modal for selecting a pre-built mock interview template.
 * Fetches template metadata from /api/v1/template/list, then creates a session via
 * /api/v1/template/start and navigates to the voice interview.
 *
 * @param {boolean} isOpen - Whether modal is visible
 * @param {function} onClose - Dismiss callback
 * @param {function} onSessionReady - Called with session_id when session is created
 */
const TemplatePicker = ({ isOpen, onClose, onSessionReady }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [startingId, setStartingId] = useState(null); // which template is spinning
  const [error, setError] = useState(null);
  const overlayRef = useRef(null);

  const candidateName =
    user?.display_name ||
    user?.name ||
    (user?.email ? user.email.split('@')[0].replace('.', ' ') : 'Candidate');

  // ── Load template list on mount ──────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    setError(null);
    setLoading(true);
    fetchTemplates()
      .then((data) => setTemplates(data.templates || []))
      .catch(() => setError('Failed to load templates. Please try again.'))
      .finally(() => setLoading(false));
  }, [isOpen]);

  // ── Close on overlay click (not on modal card click) ─────────────────────
  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  // ── Close on Escape key ───────────────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  // ── Start session ─────────────────────────────────────────────────────────
  const handleStart = async (templateId) => {
    setStartingId(templateId);
    setError(null);
    try {
      const result = await startTemplateSession(templateId);
      onSessionReady(result.session_id);
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Failed to create interview session.';
      setError(msg);
      setStartingId(null);
    }
  };

  if (!isOpen) return null;

  // Difficulty badge color
  const difficultyColor = (d) => {
    if (d === 'Hard') return { bg: '#fff0f0', text: '#ba1a1a', dot: '#ba1a1a' };
    if (d === 'Medium') return { bg: '#fff8e1', text: '#a15c00', dot: '#e08c00' };
    return { bg: '#e8f5e9', text: '#256c3d', dot: '#34a853' };
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(25, 28, 29, 0.55)',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        animation: 'fadeInOverlay 0.2s ease',
        padding: '20px',
      }}
    >
      {/* Modal Card */}
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.97)',
          borderRadius: '24px',
          boxShadow: '0 32px 80px rgba(101, 89, 123, 0.22), 0 4px 16px rgba(0,0,0,0.08)',
          width: '100%',
          maxWidth: '660px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '32px',
          position: 'relative',
          animation: 'slideUpModal 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close template picker"
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'rgba(101, 89, 123, 0.08)',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 150ms ease',
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = 'rgba(101, 89, 123, 0.16)')}
          onMouseOut={(e) => (e.currentTarget.style.background = 'rgba(101, 89, 123, 0.08)')}
        >
          <X size={18} color="#65597b" />
        </button>

        {/* Header */}
        <div style={{ marginBottom: '24px', paddingRight: '40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #65597b, #8b7fa8)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Mic size={18} color="#ffffff" />
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--on-surface)', margin: 0 }}>
              Choose Your Interview Track
            </h2>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)', margin: '0 0 12px 0', lineHeight: 1.5 }}>
            Start a full 15-question mock interview instantly — no resume or JD upload needed.
            Pick the track that matches your target role.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '999px',
                background: 'rgba(101, 89, 123, 0.08)',
                color: 'var(--primary)',
                fontSize: '12px',
                fontWeight: '600',
              }}
            >
              <User size={13} />
              <span>Interviewing as: <strong style={{ color: 'var(--on-surface)' }}>{candidateName}</strong></span>
            </span>
            <button
              onClick={() => {
                onClose();
                navigate('/settings');
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                padding: '4px 6px',
                borderRadius: '6px',
                textDecoration: 'underline',
              }}
            >
              <Edit3 size={12} />
              <span>Edit profile</span>
            </button>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div
            style={{
              background: '#ffdad6',
              borderRadius: '12px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '20px',
              fontSize: '13px',
              color: '#93000a',
              fontWeight: 500,
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                style={{
                  height: '100px',
                  borderRadius: '16px',
                  background: 'linear-gradient(90deg, #f0edf7 0%, #e8e4f3 50%, #f0edf7 100%)',
                  backgroundSize: '200% 100%',
                  animation: 'shimmer 1.5s infinite',
                }}
              />
            ))}
          </div>
        )}

        {/* Template Cards */}
        {!loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {templates.map((tpl) => {
              const isStarting = startingId === tpl.id;
              const dc = difficultyColor(tpl.difficulty);

              return (
                <div
                  key={tpl.id}
                  style={{
                    borderRadius: '16px',
                    border: '1.5px solid',
                    borderColor: isStarting ? '#65597b' : 'rgba(101, 89, 123, 0.15)',
                    background: isStarting
                      ? 'linear-gradient(135deg, rgba(101, 89, 123, 0.06), rgba(139, 127, 168, 0.04))'
                      : 'rgba(255,255,255,0.8)',
                    padding: '20px 22px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    transition: 'border-color 200ms ease, box-shadow 200ms ease, background 200ms ease',
                    cursor: isStarting || startingId ? 'default' : 'pointer',
                    boxShadow: isStarting ? '0 4px 20px rgba(101, 89, 123, 0.15)' : '0 1px 4px rgba(0,0,0,0.04)',
                  }}
                  onMouseOver={(e) => {
                    if (!startingId) {
                      e.currentTarget.style.borderColor = '#65597b';
                      e.currentTarget.style.boxShadow = '0 4px 20px rgba(101, 89, 123, 0.12)';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!startingId) {
                      e.currentTarget.style.borderColor = 'rgba(101, 89, 123, 0.15)';
                      e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.04)';
                    }
                  }}
                >
                  {/* Icon */}
                  <div
                    style={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '14px',
                      background: `linear-gradient(135deg, ${tpl.color}22, ${tpl.color}11)`,
                      border: `1.5px solid ${tpl.color}30`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {renderTemplateIcon(tpl.id, tpl.color)}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '4px' }}>
                      <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--on-surface)' }}>
                        {tpl.title}
                      </span>
                      {/* Difficulty badge */}
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '999px',
                          background: dc.bg,
                          color: dc.text,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          letterSpacing: '0.04em',
                          textTransform: 'uppercase',
                        }}
                      >
                        <span
                          style={{
                            width: '5px',
                            height: '5px',
                            borderRadius: '50%',
                            background: dc.dot,
                            display: 'inline-block',
                          }}
                        />
                        {tpl.difficulty}
                      </span>
                      {/* Q count */}
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 600,
                          color: 'var(--on-surface-variant)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '3px',
                        }}
                      >
                        <Zap size={10} />
                        {tpl.question_count}Q
                      </span>
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--on-surface-variant)', margin: '0 0 10px 0', lineHeight: 1.5 }}>
                      {tpl.description}
                    </p>
                    {/* Tech stack chips */}
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {(tpl.tech_stack || []).slice(0, 5).map((tech) => (
                        <span
                          key={tech}
                          style={{
                            fontSize: '10px',
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: '6px',
                            background: 'rgba(101, 89, 123, 0.08)',
                            color: '#65597b',
                            letterSpacing: '0.02em',
                          }}
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* CTA Button */}
                  <button
                    id={`template-start-${tpl.id}`}
                    onClick={() => handleStart(tpl.id)}
                    disabled={!!startingId}
                    aria-label={`Start ${tpl.title} mock interview`}
                    style={{
                      flexShrink: 0,
                      height: '42px',
                      padding: '0 20px',
                      borderRadius: '999px',
                      border: 'none',
                      cursor: startingId ? 'default' : 'pointer',
                      background: isStarting
                        ? 'linear-gradient(135deg, #65597b, #8b7fa8)'
                        : 'rgba(101, 89, 123, 0.1)',
                      color: isStarting ? '#ffffff' : '#65597b',
                      fontSize: '13px',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'all 200ms ease',
                      opacity: startingId && !isStarting ? 0.45 : 1,
                    }}
                    onMouseOver={(e) => {
                      if (!startingId) {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #65597b, #8b7fa8)';
                        e.currentTarget.style.color = '#ffffff';
                      }
                    }}
                    onMouseOut={(e) => {
                      if (!startingId) {
                        e.currentTarget.style.background = 'rgba(101, 89, 123, 0.1)';
                        e.currentTarget.style.color = '#65597b';
                      }
                    }}
                  >
                    {isStarting ? (
                      <>
                        <Loader2 size={14} style={{ animation: 'spin 0.8s linear infinite' }} />
                        <span>Starting…</span>
                      </>
                    ) : (
                      <>
                        <span>Start</span>
                        <ChevronRight size={14} />
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer note */}
        {!loading && (
          <p style={{ textAlign: 'center', fontSize: '12px', color: 'var(--on-surface-variant)', marginTop: '24px', marginBottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
            <Mic size={14} color="#65597b" />
            <span>Eva AI will interview you — sessions are saved to your history with a full evaluation report.</span>
          </p>
        )}
      </div>

      {/* CSS Keyframes injected via style tag */}
      <style>{`
        @keyframes fadeInOverlay {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUpModal {
          from { opacity: 0; transform: translateY(24px) scale(0.97); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default TemplatePicker;
