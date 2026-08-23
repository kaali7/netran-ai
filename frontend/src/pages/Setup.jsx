import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import useSetup from '../hooks/useSetup';
import useAuth from '../hooks/useAuth';
import AnalyzingOverlay from '../components/setup/AnalyzingOverlay';
import QuestionBankTab from '../components/setup/QuestionBankTab';
import ResumeAnalysisTab from '../components/setup/ResumeAnalysisTab';
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
  Loader2,
  AlertCircle,
  HelpCircle,
  Code,
  Layers,
  UserCheck,
} from 'lucide-react';

export const Setup = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const returnTo = location.state?.from || '/dashboard';

  const {
    sessionId,
    parsedResume,
    parsedJD,
    questionPreview,
    phase,
    progressMsg,
    error,
    isResumeUploading,
    isJdExtracting,
    isPipelineRunning,
    isCompleted,
    isCacheAutofilled,
    handleResumeUpload: uploadResumeFile,
    handleJdSubmit: submitJdText,
    handleStartPipeline,
  } = useSetup();

  // Local state for interactive form controls
  const [trackTitle, setTrackTitle] = useState(location.state?.role_title || 'Custom Technical Practice Track');
  const [targetLevel, setTargetLevel] = useState(location.state?.target_level || 'Mid-Level');
  const [jdText, setJdText] = useState(location.state?.jd_text || '');
  const [attachedJdFileName, setAttachedJdFileName] = useState('');
  const [resumeFileName, setResumeFileName] = useState('');
  const [resumeFileSize, setResumeFileSize] = useState('');
  const [personaMode, setPersonaMode] = useState('supportive'); // 'supportive' | 'fast-paced'
  const [activeTab, setActiveTab] = useState('resume'); // 'questions' | 'resume'

  const targetLevels = ['Junior', 'Mid-Level', 'Senior'];

  // Update track title automatically when parsed JD is available
  useEffect(() => {
    if (parsedJD?.role_title) {
      setTrackTitle(parsedJD.role_title);
    }
  }, [parsedJD]);

  // Automatically switch tab to 'questions' when question tree pipeline finishes
  useEffect(() => {
    if (isCompleted && questionPreview?.question_tree?.length > 0) {
      setActiveTab('questions');
    }
  }, [isCompleted, questionPreview]);

  // Handle JD File Upload
  const handleJdFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setAttachedJdFileName(file.name);
    try {
      const text = await file.text();
      setJdText(text);
      await submitJdText(text);
    } catch (err) {
      console.error('Failed to read JD file:', err);
    }
  };

  // Handle Resume Upload
  const onResumeFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setResumeFileName(file.name);
    setResumeFileSize(`${Math.round(file.size / 1024)} KB`);
    try {
      await uploadResumeFile(file);
      setActiveTab('resume');
    } catch (err) {
      console.error('Resume upload error:', err);
    }
  };

  // Handle JD Text Blur / Ingest trigger
  const handleJdBlur = async () => {
    if (jdText && jdText.trim().length >= 50) {
      try {
        await submitJdText(jdText);
      } catch (err) {
        console.error('JD ingest blur error:', err);
      }
    }
  };

  // Handle Launch CTA Click
  const handleLaunchTrackClick = async () => {
    if (isCompleted && sessionId) {
      navigate(`/interview/${sessionId}`, { state: { from: returnTo } });
      return;
    }

    // Trigger Stage 1 & 2 pipeline
    try {
      await handleStartPipeline(targetLevel);
    } catch (err) {
      console.error('Launch pipeline error:', err);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', paddingBottom: '60px', position: 'relative' }}>
      
      {/* ── Cache Autofill Toast ───────────────────────────────────────────── */}
      {isCacheAutofilled && (
        <div
          style={{
            position: 'absolute',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--primary-container)',
            color: 'var(--on-primary-container)',
            padding: '10px 20px',
            borderRadius: '9999px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(101, 89, 123, 0.2)',
            zIndex: 100,
            animation: 'fadeInDown 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
          }}
        >
          <Zap size={16} fill="currentColor" />
          <span style={{ fontSize: '13px', fontWeight: '700' }}>Instant Resume & JD Match! Restored from Cache.</span>
        </div>
      )}

      {/* ── Top Bar Header ────────────────────────────────────────────────── */}
      <header
        className="navbar-inner-container"
        style={{
          width: '100%',
          maxWidth: 'var(--container-max)',
          margin: '0 auto',
          padding: '16px 36px 12px 36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <button
          onClick={() => navigate(returnTo)}
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
          <span>{returnTo === '/history' ? 'Back to History' : 'Back to Dashboard'}</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
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
              {user?.email?.charAt(0).toUpperCase() || 'C'}
            </div>
            <span className="desktop-nav-user-text" style={{ fontSize: '14px', fontWeight: '600', color: 'var(--on-surface)' }}>
              {user?.email || 'Candidate'}
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Container ────────────────────────────────────────────────── */}
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
            Upload candidate resume and job description to build a custom technical interview engine.
          </p>
        </div>

        {/* Error Alert Banner */}
        {error && (
          <div
            style={{
              background: 'var(--error-container)',
              color: 'var(--on-error-container)',
              padding: '14px 20px',
              borderRadius: '14px',
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '14px',
              fontWeight: '600',
            }}
          >
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* ── 2-Column Split Layout ──────────────────────────────────────── */}
        <div className="dashboard-split-grid animate-entrance animate-delay-1" style={{ alignItems: 'start' }}>
          
          {/* ── LEFT COLUMN: TRACK DEFINITION & CONTEXT ──────────────────── */}
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

            {/* Candidate Resume Upload Section */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <label className="text-label-xs">CANDIDATE RESUME</label>
                {isResumeUploading && (
                  <span style={{ fontSize: '12px', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600' }}>
                    <Loader2 size={13} style={{ animation: 'spin 0.8s linear infinite' }} />
                    Parsing via Gemini...
                  </span>
                )}
              </div>

              {parsedResume ? (
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
                      <div style={{ fontWeight: '700', fontSize: '14px', color: '#1e4831' }}>
                        {resumeFileName || parsedResume.name || 'Candidate_Resume.pdf'}
                      </div>
                      <div style={{ fontSize: '12px', color: '#447358', marginTop: '2px' }}>
                        {resumeFileSize || 'Extracted via Gemini'} • Ready
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
                    <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={onResumeFileChange} style={{ display: 'none' }} />
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
                    transition: 'border-color 180ms ease',
                  }}
                >
                  <Upload size={24} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
                  <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--on-surface)' }}>
                    Click to upload candidate resume (PDF/DOCX)
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--on-surface-variant)', marginTop: '4px' }}>
                    Gemini will extract candidate profile & skills automatically
                  </span>
                  <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={onResumeFileChange} style={{ display: 'none' }} />
                </label>
              )}
            </div>

            {/* Job Description Context */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <label className="text-label-xs">JOB DESCRIPTION CONTEXT</label>
                {isJdExtracting && (
                  <span style={{ fontSize: '12px', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600' }}>
                    <Loader2 size={13} style={{ animation: 'spin 0.8s linear infinite' }} />
                    Extracting topics...
                  </span>
                )}
              </div>

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
                  onBlur={handleJdBlur}
                  placeholder="Paste target job description text here (min 50 chars)..."
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
                      {attachedJdFileName ? `Attached: ${attachedJdFileName}` : 'Or attach text file'}
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


          </Card>

          {/* ── RIGHT COLUMN: ANALYSIS & QUESTION BANK (2 CLEAN TABS) ──────── */}
          <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px', minHeight: '560px' }}>
            
            {/* Header / Tab Navigation Bar (2 Clean Tabs) */}
            <div style={{ borderBottom: '1px solid rgba(101, 89, 123, 0.12)', pb: '12px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setActiveTab('questions')}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    borderRadius: '9999px',
                    fontSize: '13px',
                    fontWeight: '700',
                    border: 'none',
                    cursor: 'pointer',
                    background: activeTab === 'questions' ? 'var(--primary)' : 'rgba(101, 89, 123, 0.08)',
                    color: activeTab === 'questions' ? '#ffffff' : 'var(--on-surface-variant)',
                    transition: 'all 180ms ease',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <Layers size={15} />
                  <span>Question Bank</span>
                  {questionPreview?.question_tree?.length > 0 && (
                    <span
                      style={{
                        background: activeTab === 'questions' ? 'rgba(255,255,255,0.25)' : 'var(--primary-container)',
                        color: activeTab === 'questions' ? '#ffffff' : 'var(--on-primary-container)',
                        padding: '1px 6px',
                        borderRadius: '9999px',
                        fontSize: '11px',
                      }}
                    >
                      {questionPreview.question_tree.length}
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('resume')}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    borderRadius: '9999px',
                    fontSize: '13px',
                    fontWeight: '700',
                    border: 'none',
                    cursor: 'pointer',
                    background: activeTab === 'resume' ? 'var(--primary)' : 'rgba(101, 89, 123, 0.08)',
                    color: activeTab === 'resume' ? '#ffffff' : 'var(--on-surface-variant)',
                    transition: 'all 180ms ease',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <UserCheck size={15} />
                  <span>Resume & Profile Analysis</span>
                </button>
              </div>
            </div>

            {/* TAB CONTENT 1: QUESTION BANK */}
            {activeTab === 'questions' && (
              <QuestionBankTab questions={questionPreview?.question_tree || []} />
            )}

            {/* TAB CONTENT 2: RESUME & PROFILE ANALYSIS */}
            {activeTab === 'resume' && (
              <ResumeAnalysisTab
                resumeAnalysis={questionPreview?.resume_analysis}
                parsedResume={parsedResume}
              />
            )}
          </Card>
        </div>

        {/* ── Bottom Center Action CTA ────────────────────────────────────── */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '36px' }} className="animate-entrance animate-delay-2">
          <button
            onClick={handleLaunchTrackClick}
            disabled={isPipelineRunning}
            className="btn btn-primary"
            style={{
              padding: '16px 36px',
              fontSize: '15px',
              fontWeight: '700',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: isCompleted
                ? 'linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%)'
                : 'linear-gradient(135deg, #514467 0%, #3a2e4f 100%)',
              boxShadow: '0 8px 24px rgba(60, 45, 80, 0.35)',
              cursor: isPipelineRunning ? 'not-allowed' : 'pointer',
              opacity: isPipelineRunning ? 0.7 : 1,
            }}
          >
            <Rocket size={18} />
            <span>
              {isCompleted ? 'START VOICE INTERVIEW ROOM' : 'BUILD & LAUNCH TRACK'}
            </span>
          </button>
        </div>
      </PageWrapper>

      {/* ── Pipeline Execution Overlay ───────────────────────────────────── */}
      <AnalyzingOverlay isOpen={isPipelineRunning} progressMsg={progressMsg} />
    </div>
  );
};

export default Setup;
