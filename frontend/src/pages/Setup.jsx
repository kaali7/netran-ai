import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import {
  ArrowLeft,
  Settings,
  Pin,
  Zap,
  FileText,
  FileCheck,
  CheckCircle2,
  Clock,
  Rocket,
  Sparkles,
  Upload,
  User,
  ShieldCheck,
} from 'lucide-react';

export const Setup = () => {
  const navigate = useNavigate();

  // State management for interactive form controls
  const [trackTitle, setTrackTitle] = useState('Fullstack Software Engineer');
  const [targetLevel, setTargetLevel] = useState('Mid-Level');
  const [jdText, setJdText] = useState('');
  const [attachedJdFileName, setAttachedJdFileName] = useState('');
  const [resumeFile, setResumeFile] = useState({
    name: 'Arjun_Fullstack_CV.pdf',
    size: '428 KB',
    uploaded: true,
  });
  const [personaMode, setPersonaMode] = useState('supportive'); // 'supportive' | 'fast-paced'

  const targetLevels = ['Junior', 'Mid-Level', 'Senior'];

  const topicWeights = [
    { title: 'System Design & APIs', pct: 35, color: 'var(--primary)' },
    { title: 'Frontend (React/Next.js)', pct: 30, color: 'var(--secondary)' },
    { title: 'Databases & Caching', pct: 20, color: '#4a6fa5' },
    { title: 'Core CS & Algorithms', pct: 15, color: '#8e5b9f' },
  ];

  const extractedKeywords = [
    { label: 'React.js', bg: '#e8e5ff', color: '#5642a6' },
    { label: 'Node.js', bg: '#dcfce7', color: '#15803d' },
    { label: 'Raft Consensus', bg: '#ffedd5', color: '#c2410c' },
    { label: 'Redis Mutex', bg: '#ffe4e6', color: '#be123c' },
    { label: 'PostgreSQL', bg: '#e0f2fe', color: '#0369a1' },
    { label: 'Kafka', bg: '#f1f5f9', color: '#475569' },
    { label: 'System Architecture', bg: '#f3e8ff', color: '#6b21a8' },
  ];

  const handleJdFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAttachedJdFileName(file.name);
    }
  };

  const handleResumeUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setResumeFile({
        name: file.name,
        size: `${Math.round(file.size / 1024)} KB`,
        uploaded: true,
      });
    }
  };

  const handleLaunchTrack = () => {
    // Navigate to interview session room (or fallback)
    navigate('/interview/sess_custom_track');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', paddingBottom: '60px' }}>
      {/* Top Bar Header */}
      <header
        style={{
          width: '100%',
          maxWidth: 'var(--container-max)',
          margin: '0 auto',
          padding: '24px 24px 12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <button
          onClick={() => navigate('/dashboard')}
          className="btn btn-ghost"
          style={{
            borderRadius: '9999px',
            padding: '8px 18px',
            fontSize: '14px',
            gap: '8px',
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', color: 'var(--primary)' }}>
            <Sparkles size={18} />
            <span>Netran AI</span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(255, 255, 255, 0.85)',
              padding: '6px 14px',
              borderRadius: '9999px',
              border: '1px solid rgba(0, 0, 0, 0.06)',
            }}
          >
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--primary-container)',
                color: 'var(--on-primary-container)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '700',
                fontSize: '12px',
              }}
            >
              AS
            </div>
            <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--on-surface)' }}>Arjun S.</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <PageWrapper>
        {/* Title Section */}
        <div style={{ marginBottom: '28px' }} className="animate-entrance">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'rgba(101, 89, 123, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
              }}
            >
              <Settings size={22} />
            </div>
            <h1 className="text-headline-xl">Configure New Practice Track</h1>
          </div>
          <p className="text-body-md" style={{ marginLeft: '48px' }}>
            Set up parameters to generate your custom Fullstack interview engine.
          </p>
        </div>

        {/* 2-Column Split Grid Layout */}
        <div className="dashboard-split-grid animate-entrance animate-delay-1" style={{ alignItems: 'start' }}>
          {/* LEFT COLUMN: TRACK DEFINITION & CONTEXT */}
          <Card style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Pin size={18} style={{ color: 'var(--outline)' }} />
              <span className="text-label-xs" style={{ fontSize: '12px', letterSpacing: '0.08em' }}>
                TRACK DEFINITION & CONTEXT
              </span>
            </div>

            {/* Track Title */}
            <div>
              <label className="text-label-xs" style={{ display: 'block', marginBottom: '8px' }}>
                TRACK TITLE
              </label>
              <input
                type="text"
                value={trackTitle}
                onChange={(e) => setTrackTitle(e.target.value)}
                placeholder="e.g. Fullstack Software Engineer"
                style={{
                  width: '100%',
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-lg)',
                  border: '1.5px solid var(--outline-variant)',
                  background: 'var(--surface-container-low)',
                  fontSize: '15px',
                  fontWeight: '600',
                  color: 'var(--on-surface)',
                  outline: 'none',
                  transition: 'all 180ms ease',
                }}
              />
            </div>

            {/* Target Level Pills */}
            <div>
              <label className="text-label-xs" style={{ display: 'block', marginBottom: '8px' }}>
                TARGET LEVEL
              </label>
              <div style={{ display: 'flex', gap: '10px' }}>
                {targetLevels.map((lvl) => {
                  const isActive = targetLevel === lvl;
                  return (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setTargetLevel(lvl)}
                      style={{
                        flex: 1,
                        padding: '10px 16px',
                        borderRadius: 'var(--radius-full)',
                        border: isActive ? '1.5px solid var(--primary)' : '1.5px solid var(--outline-variant)',
                        background: isActive ? 'var(--primary)' : '#ffffff',
                        color: isActive ? '#ffffff' : 'var(--on-surface)',
                        fontWeight: isActive ? '700' : '600',
                        fontSize: '14px',
                        cursor: 'pointer',
                        transition: 'all 180ms cubic-bezier(0.16, 1, 0.3, 1)',
                        boxShadow: isActive ? '0 4px 12px rgba(101, 89, 123, 0.25)' : 'none',
                      }}
                    >
                      {lvl}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Job Description Context */}
            <div>
              <label className="text-label-xs" style={{ display: 'block', marginBottom: '8px' }}>
                JOB DESCRIPTION CONTEXT
              </label>
              <div
                style={{
                  borderRadius: 'var(--radius-lg)',
                  border: '1.5px solid var(--outline-variant)',
                  background: 'var(--surface-container-low)',
                  overflow: 'hidden',
                }}
              >
                <textarea
                  rows={4}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste full JD text..."
                  style={{
                    width: '100%',
                    padding: '16px',
                    border: 'none',
                    background: 'transparent',
                    resize: 'vertical',
                    fontSize: '14px',
                    fontFamily: 'inherit',
                    color: 'var(--on-surface)',
                    outline: 'none',
                  }}
                />
                <div
                  style={{
                    padding: '10px 16px',
                    borderTop: '1px solid rgba(0, 0, 0, 0.05)',
                    background: 'rgba(255, 255, 255, 0.7)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '13px',
                    color: 'var(--on-surface-variant)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={15} />
                    <span>
                      {attachedJdFileName ? `Attached: ${attachedJdFileName}` : 'Or attach file: No file selected'}
                    </span>
                  </div>
                  <label
                    style={{
                      cursor: 'pointer',
                      fontWeight: '600',
                      color: 'var(--primary)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(101, 89, 123, 0.08)',
                    }}
                  >
                    Browse
                    <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={handleJdFileUpload} style={{ display: 'none' }} />
                  </label>
                </div>
              </div>
            </div>

            {/* Candidate Resume */}
            <div>
              <label className="text-label-xs" style={{ display: 'block', marginBottom: '8px' }}>
                CANDIDATE RESUME
              </label>
              {resumeFile.uploaded ? (
                <div
                  style={{
                    background: '#eef8f2',
                    border: '1.5px solid #c8e8d5',
                    borderRadius: 'var(--radius-lg)',
                    padding: '14px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background: '#3a7d58',
                        color: '#ffffff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <FileCheck size={22} />
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '14px', color: '#1e4831' }}>{resumeFile.name}</div>
                      <div style={{ fontSize: '12px', color: '#447358', marginTop: '2px' }}>
                        {resumeFile.size} • Uploaded
                      </div>
                    </div>
                  </div>
                  <label
                    style={{
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '600',
                      color: '#2a5e40',
                      textDecoration: 'underline',
                    }}
                  >
                    Change
                    <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} style={{ display: 'none' }} />
                  </label>
                </div>
              ) : (
                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '24px',
                    borderRadius: 'var(--radius-lg)',
                    border: '2px dashed var(--outline-variant)',
                    background: 'var(--surface-container-low)',
                    cursor: 'pointer',
                  }}
                >
                  <Upload size={24} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
                  <span style={{ fontSize: '14px', fontWeight: '600' }}>Click to upload resume (PDF/DOCX)</span>
                  <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} style={{ display: 'none' }} />
                </label>
              )}
            </div>
          </Card>

          {/* RIGHT COLUMN: TOPIC MATRIX & FOCUS WEIGHTS */}
          <Card style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={18} style={{ color: 'var(--secondary)' }} />
              <span className="text-label-xs" style={{ fontSize: '12px', letterSpacing: '0.08em' }}>
                TOPIC MATRIX & FOCUS WEIGHTS
              </span>
            </div>

            {/* Topic Progress Weight Rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {topicWeights.map((t) => (
                <div key={t.title}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '14px' }}>
                    <span style={{ fontWeight: '600', color: 'var(--on-surface)' }}>{t.title}</span>
                    <span style={{ fontWeight: '700', color: 'var(--on-surface-variant)' }}>{t.pct}%</span>
                  </div>
                  <div
                    style={{
                      height: '8px',
                      width: '100%',
                      background: 'var(--surface-container-high)',
                      borderRadius: 'var(--radius-full)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${t.pct}%`,
                        background: t.color,
                        borderRadius: 'var(--radius-full)',
                        transition: 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Extracted Keywords */}
            <div>
              <label className="text-label-xs" style={{ display: 'block', marginBottom: '12px' }}>
                EXTRACTED KEYWORDS
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {extractedKeywords.map((kw) => (
                  <span
                    key={kw.label}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 14px',
                      borderRadius: 'var(--radius-full)',
                      background: kw.bg,
                      color: kw.color,
                      fontSize: '13px',
                      fontWeight: '700',
                    }}
                  >
                    <span>{kw.label}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Interviewer Persona Mode */}
            <div>
              <label className="text-label-xs" style={{ display: 'block', marginBottom: '12px' }}>
                INTERVIEWER PERSONA MODE
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* Supportive Mode Card */}
                <div
                  onClick={() => setPersonaMode('supportive')}
                  style={{
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-lg)',
                    border:
                      personaMode === 'supportive'
                        ? '2px solid var(--primary)'
                        : '1.5px solid var(--outline-variant)',
                    background: personaMode === 'supportive' ? '#fbf9fe' : '#ffffff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 180ms cubic-bezier(0.16, 1, 0.3, 1)',
                    boxShadow: personaMode === 'supportive' ? '0 4px 16px rgba(101, 89, 123, 0.08)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '38px',
                        height: '38px',
                        borderRadius: '50%',
                        background: 'rgba(101, 89, 123, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--primary)',
                      }}
                    >
                      <Sparkles size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '14px', color: 'var(--on-surface)' }}>
                        Supportive & Structured Conversation
                      </div>
                      <div style={{ fontSize: '13px', color: 'var(--on-surface-variant)', marginTop: '2px' }}>
                        Guides through problems with hints.
                      </div>
                    </div>
                  </div>
                  {personaMode === 'supportive' && <CheckCircle2 size={20} style={{ color: 'var(--primary)' }} />}
                </div>

                {/* Fast-Paced Technical Drill Card */}
                <div
                  onClick={() => setPersonaMode('fast-paced')}
                  style={{
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-lg)',
                    border:
                      personaMode === 'fast-paced'
                        ? '2px solid var(--primary)'
                        : '1.5px solid var(--outline-variant)',
                    background: personaMode === 'fast-paced' ? '#fbf9fe' : '#ffffff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 180ms cubic-bezier(0.16, 1, 0.3, 1)',
                    boxShadow: personaMode === 'fast-paced' ? '0 4px 16px rgba(101, 89, 123, 0.08)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '38px',
                        height: '38px',
                        borderRadius: '50%',
                        background: 'rgba(0, 0, 0, 0.04)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--outline)',
                      }}
                    >
                      <Clock size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '14px', color: 'var(--on-surface)' }}>
                        Fast-Paced Technical Drill
                      </div>
                      <div style={{ fontSize: '13px', color: 'var(--on-surface-variant)', marginTop: '2px' }}>
                        Rapid fire questions, strict evaluation.
                      </div>
                    </div>
                  </div>
                  {personaMode === 'fast-paced' && <CheckCircle2 size={20} style={{ color: 'var(--primary)' }} />}
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Floating / Bottom Center Action CTA */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '36px' }} className="animate-entrance animate-delay-2">
          <button
            onClick={handleLaunchTrack}
            className="btn btn-primary"
            style={{
              padding: '16px 36px',
              fontSize: '15px',
              fontWeight: '700',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'linear-gradient(135deg, #514467 0%, #3a2e4f 100%)',
              boxShadow: '0 8px 24px rgba(60, 45, 80, 0.35)',
              transition: 'transform 180ms ease, box-shadow 180ms ease',
            }}
          >
            <Rocket size={18} />
            <span>BUILD & LAUNCH TRACK</span>
          </button>
        </div>
      </PageWrapper>
    </div>
  );
};

export default Setup;
