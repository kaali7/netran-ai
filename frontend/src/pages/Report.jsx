import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  RotateCcw,
  BarChart2,
  Share2,
  Calendar,
  Clock,
  User,
  Lightbulb,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Mic,
  Award,
  Sparkles,
  BookOpen,
  ShieldAlert,
  FileText,
  Cpu,
  TrendingUp,
} from 'lucide-react';
import Card from '../components/ui/Card';
import useReports from '../hooks/useReports';

export const Report = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const { report, status, progressMessage, isLoading, error } = useReports(sessionId);

  // Accordion state for turn breakdown
  const [expandedQuestions, setExpandedQuestions] = useState({});

  // Initialize first turn open when report loads
  useEffect(() => {
    if (report && report.turn_evaluations && report.turn_evaluations.length > 0) {
      setExpandedQuestions({ 0: true });
    }
  }, [report]);

  const toggleQuestion = (index) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  // Helper for color styling hiring signal badge
  const getHiringSignalStyle = (signal) => {
    switch (signal?.toLowerCase()) {
      case 'strong hire':
        return { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' };
      case 'hire':
        return { bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' };
      case 'lean no hire':
        return { bg: '#fef3c7', text: '#b45309', border: '#fde68a' };
      case 'no hire':
        return { bg: '#fee2e2', text: '#b91c1c', border: '#fca5a5' };
      default:
        return { bg: '#f3e8ff', text: '#6b21a8', border: '#e9d5ff' };
    }
  };

  // Helper for formatting ISO date
  const formatDate = (isoString) => {
    if (!isoString) return new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    try {
      return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return isoString;
    }
  };

  // Loading Skeleton View
  if (isLoading || status === 'evaluating') {
    return (
      <div style={{ background: '#f8f9fa', minHeight: '100vh', padding: '60px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-family, system-ui)' }}>
        <Card style={{ padding: '40px', maxWidth: '520px', width: '100%', textAlign: 'center', background: '#ffffff', borderRadius: '24px', boxShadow: '0 12px 36px rgba(0,0,0,0.04)' }}>
          <Cpu size={44} style={{ color: '#65597b', marginBottom: '20px' }} className="animate-spin" />
          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#111827', marginBottom: '10px' }}>
            Preparing Evaluation Scorecard...
          </h2>
          <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '24px', lineHeight: '1.5' }}>
            {progressMessage || 'Gemini 3.6 Flash multimodal engine is evaluating turn transcripts and audio metrics.'}
          </p>
          <button
            onClick={() => navigate(`/processing/${sessionId}`)}
            style={{
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
            View Live Processing Progress
          </button>
        </Card>
      </div>
    );
  }

  // Error State View
  if (error || !report) {
    return (
      <div style={{ background: '#f8f9fa', minHeight: '100vh', padding: '60px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Card style={{ padding: '40px', maxWidth: '520px', width: '100%', textAlign: 'center', background: '#ffffff', borderRadius: '24px' }}>
          <AlertTriangle size={44} style={{ color: '#dc2626', marginBottom: '20px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#111827', marginBottom: '10px' }}>
            Report Not Found or Processing
          </h2>
          <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '24px' }}>
            {error || 'No evaluation report artifact could be located for this session yet.'}
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button
              onClick={() => navigate(`/processing/${sessionId}`)}
              style={{ padding: '10px 18px', borderRadius: '9999px', background: '#65597b', color: '#ffffff', border: 'none', fontWeight: '700', fontSize: '13px', cursor: 'pointer' }}
            >
              Check Processing Status
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              style={{ padding: '10px 18px', borderRadius: '9999px', background: '#f3f4f6', color: '#374151', border: '1px solid #e5e7eb', fontWeight: '600', fontSize: '13px', cursor: 'pointer' }}
            >
              Go to Dashboard
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // Destructure real report fields from CandidateReportPayload
  const {
    overall_hiring_signal = 'Hire',
    overall_technical_score = 80,
    overall_vocal_confidence_score = 85,
    technical_pillars = [],
    behavioral_flags = [],
    candidate_feedback = {},
    turn_evaluations = [],
    executive_summary = 'Candidate demonstrated solid technical understanding across system architecture concepts.',
    generated_at,
  } = report;

  const signalStyle = getHiringSignalStyle(overall_hiring_signal);

  // Compute aggregate filler word count across turns
  const totalFillerWords = turn_evaluations.reduce((acc, t) => acc + (t.filler_word_count || 0), 0);

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px', fontFamily: 'var(--font-family, system-ui)' }}>
      {/* Top Header Bar */}
      <header
        style={{
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: '16px 32px',
        }}
      >
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Netran AI Brand */}
          <div
            onClick={() => navigate('/dashboard')}
            style={{
              cursor: 'pointer',
              fontWeight: '800',
              fontSize: '20px',
              color: '#65597b',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Sparkles size={20} />
            <span>Netran AI</span>
          </div>

          {/* Right Header Navigation */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'transparent',
                border: 'none',
                color: '#4b5563',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              <ArrowLeft size={16} />
              <span>Back to Dashboard</span>
            </button>

            {/* Profile Avatar Pill */}
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: '#f3e8ff',
                color: '#65597b',
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
        </div>
      </header>

      {/* Main Page Container */}
      <div style={{ maxWidth: '1200px', margin: '32px auto 0 auto', padding: '0 24px' }}>
        
        {/* SESSION SUMMARY BANNER CARD */}
        <Card
          style={{
            marginBottom: '24px',
            padding: '28px 32px',
            background: '#ffffff',
            borderRadius: '24px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.03)',
          }}
          className="animate-entrance"
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '20px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <h1
                  style={{
                    fontSize: '26px',
                    fontWeight: '800',
                    color: '#111827',
                    letterSpacing: '-0.02em',
                    margin: 0,
                  }}
                >
                  Multimodal Evaluation Scorecard
                </h1>
                <span style={{ fontSize: '24px' }}>🎯</span>
              </div>

              {/* Session Meta Information */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  marginTop: '12px',
                  color: '#6b7280',
                  fontSize: '14px',
                  fontWeight: '500',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <User size={15} />
                  <span>Interviewed by Eva (AI)</span>
                </div>
                <span>•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={15} />
                  <span>Completed {formatDate(generated_at)}</span>
                </div>
                <span>•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={15} />
                  <span>Turns Evaluated: {turn_evaluations.length}</span>
                </div>
              </div>
            </div>

            {/* Banner Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <button
                onClick={() => navigate('/setup')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: '9999px',
                  background: '#f3e8ff',
                  color: '#65597b',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={15} />
                <span>Retake Practice Track</span>
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: '9999px',
                  background: '#ffffff',
                  color: '#374151',
                  border: '1px solid #e5e7eb',
                  fontWeight: '600',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                <Share2 size={15} />
                <span>Dashboard</span>
              </button>
            </div>
          </div>
        </Card>

        {/* TOP ROW GRID: OVERALL READINESS & SKILL MATRIX */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '24px',
            marginBottom: '24px',
          }}
        >
          {/* OVERALL READINESS CARD */}
          <Card
            style={{
              padding: '28px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#111827', margin: '0 0 20px 0' }}>
              Overall Technical Score
            </h2>

            {/* Circular Donut Gauge */}
            <div style={{ position: 'relative', width: '160px', height: '160px', margin: '0 auto 16px auto' }}>
              <svg width="160" height="160" viewBox="0 0 160 160">
                {/* Background Ring */}
                <circle cx="80" cy="80" r="62" fill="none" stroke="#f3f4f6" strokeWidth="14" />
                {/* Active Progress Arc */}
                <circle
                  cx="80"
                  cy="80"
                  r="62"
                  fill="none"
                  stroke="#65597b"
                  strokeWidth="14"
                  strokeDasharray={2 * Math.PI * 62}
                  strokeDashoffset={2 * Math.PI * 62 * (1 - Math.min(100, Math.max(0, overall_technical_score)) / 100)}
                  strokeLinecap="round"
                  transform="rotate(-90 80 80)"
                  style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
              </svg>

              {/* Score Center Text */}
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '36px', fontWeight: '800', color: '#111827', lineHeight: '1' }}>
                  {overall_technical_score}
                </span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#6b7280', marginTop: '2px' }}>
                  / 100
                </span>
              </div>
            </div>

            {/* Hiring Signal Badge Chip */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: signalStyle.bg,
                color: signalStyle.text,
                border: `1px solid ${signalStyle.border}`,
                padding: '6px 18px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: '700',
                marginBottom: '24px',
              }}
            >
              <Award size={15} />
              <span>Hiring Signal: {overall_hiring_signal}</span>
            </div>

            {/* Vocal Performance Sub-Card */}
            <div
              style={{
                width: '100%',
                background: '#f9fafb',
                borderRadius: '16px',
                padding: '16px',
                border: '1px solid #f3f4f6',
                textAlign: 'left',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  color: '#6b7280',
                  letterSpacing: '0.05em',
                  marginBottom: '12px',
                  textTransform: 'uppercase',
                }}
              >
                Vocal & Speech Telemetry
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#374151', fontSize: '13px', fontWeight: '500' }}>
                    <Zap size={14} style={{ color: '#6b7280' }} />
                    <span>Vocal Confidence</span>
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: '#15803d' }}>
                    {overall_vocal_confidence_score} / 100
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#374151', fontSize: '13px', fontWeight: '500' }}>
                    <Mic size={14} style={{ color: '#6b7280' }} />
                    <span>Est. Filler Words</span>
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: totalFillerWords > 8 ? '#dc2626' : '#15803d' }}>
                    {totalFillerWords} words
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* SKILL BREAKDOWN MATRIX CARD */}
          <Card
            style={{
              padding: '28px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#111827', margin: '0 0 20px 0' }}>
                Technical Domain Pillars
              </h2>

              {/* Skill Bars */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {technical_pillars.length > 0 ? (
                  technical_pillars.map((pillar, pIdx) => (
                    <div key={pIdx}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                        <span>{pillar.pillar_name}</span>
                        <span style={{ fontWeight: '700' }}>{pillar.score}%</span>
                      </div>
                      <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                        <div style={{ width: `${pillar.score}%`, height: '100%', background: '#65597b', borderRadius: '9999px' }} />
                      </div>
                      {pillar.summary && (
                        <p style={{ fontSize: '11px', color: '#6b7280', margin: '4px 0 0 0', lineHeight: '1.4' }}>
                          {pillar.summary}
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '13px', color: '#6b7280', fontStyle: 'italic' }}>
                    No pillar breakdown scores generated.
                  </div>
                )}
              </div>
            </div>

            {/* AI Executive Summary Box */}
            <div
              style={{
                marginTop: '24px',
                background: '#f5f0fb',
                borderRadius: '16px',
                padding: '18px 20px',
                border: '1px solid #e9d8fd',
                display: 'flex',
                gap: '14px',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#65597b',
                  flexShrink: 0,
                  boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
                }}
              >
                <Lightbulb size={17} />
              </div>

              <div>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#65597b', marginBottom: '4px' }}>
                  Executive AI Summary
                </div>
                <p style={{ fontSize: '13px', color: '#49454d', margin: 0, lineHeight: '1.5' }}>
                  {executive_summary}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* BEHAVIORAL FLAGS CARD (IF ANY) */}
        {behavioral_flags.length > 0 && (
          <Card style={{ padding: '24px 28px', background: '#fff1f2', borderRadius: '20px', border: '1px solid #fecdd3', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <ShieldAlert size={20} style={{ color: '#e11d48' }} />
              <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#9f1239', margin: 0 }}>
                Observed Behavioral & Telemetry Flags ({behavioral_flags.length})
              </h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {behavioral_flags.map((flag, idx) => (
                <div key={idx} style={{ background: '#ffffff', padding: '12px 16px', borderRadius: '12px', border: '1px solid #ffe4e6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '800', padding: '3px 8px', borderRadius: '9999px', background: flag.severity === 'CRITICAL' ? '#fee2e2' : '#fef3c7', color: flag.severity === 'CRITICAL' ? '#991b1b' : '#92400e' }}>
                      {flag.severity}
                    </span>
                    <span style={{ fontSize: '13px', color: '#374151', fontWeight: '500' }}>
                      {flag.description}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600' }}>
                    Turn #{flag.turn_id}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* CANDIDATE FEEDBACK & STUDY ROADMAP */}
        {candidate_feedback && (candidate_feedback.key_strengths || candidate_feedback.primary_growth_areas) && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', marginBottom: '24px' }}>
            {/* Strengths */}
            <Card style={{ padding: '24px', background: '#ffffff', borderRadius: '20px', border: '1px solid rgba(229, 231, 235, 0.8)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#15803d', fontWeight: '700', fontSize: '15px' }}>
                <CheckCircle2 size={18} />
                <span>Key Technical Strengths</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(candidate_feedback.key_strengths || []).map((str, i) => (
                  <li key={i} style={{ fontSize: '13px', color: '#374151', lineHeight: '1.5' }}>
                    {str}
                  </li>
                ))}
              </ul>
            </Card>

            {/* Growth Areas */}
            <Card style={{ padding: '24px', background: '#ffffff', borderRadius: '20px', border: '1px solid rgba(229, 231, 235, 0.8)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#b45309', fontWeight: '700', fontSize: '15px' }}>
                <TrendingUp size={18} />
                <span>Primary Growth Areas</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(candidate_feedback.primary_growth_areas || []).map((area, i) => (
                  <li key={i} style={{ fontSize: '13px', color: '#374151', lineHeight: '1.5' }}>
                    {area}
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        )}

        {/* RECOMMENDED STUDY TOPICS */}
        {candidate_feedback?.recommended_topics_to_study?.length > 0 && (
          <Card style={{ padding: '24px 28px', background: '#ffffff', borderRadius: '20px', border: '1px solid rgba(229, 231, 235, 0.8)', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: '#65597b', fontWeight: '700', fontSize: '15px' }}>
              <BookOpen size={18} />
              <span>Recommended Topics & Frameworks to Study</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {candidate_feedback.recommended_topics_to_study.map((topic, i) => (
                <span key={i} style={{ fontSize: '13px', fontWeight: '600', padding: '6px 14px', borderRadius: '9999px', background: '#f5f0fb', color: '#65597b', border: '1px solid #e9d8fd' }}>
                  📚 {topic}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* BOTTOM SECTION: QUESTION-BY-QUESTION BREAKDOWN WITH EVA */}
        <Card
          style={{
            padding: '28px',
            background: '#ffffff',
            borderRadius: '24px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
          }}
        >
          {/* Section Title */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <MessageSquare size={18} style={{ color: '#65597b' }} />
            <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#374151', letterSpacing: '0.04em', margin: 0, textTransform: 'uppercase' }}>
              Question-By-Question Breakdown With Eva ({turn_evaluations.length} Turns)
            </h2>
          </div>

          {/* Turn Accordions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {turn_evaluations.length > 0 ? (
              turn_evaluations.map((t, idx) => {
                const isExpanded = expandedQuestions[idx];

                return (
                  <div
                    key={t.turn_id || idx}
                    style={{
                      border: '1px solid #e5e7eb',
                      borderRadius: '16px',
                      overflow: 'hidden',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {/* Accordion Header */}
                    <div
                      onClick={() => toggleQuestion(idx)}
                      style={{
                        padding: '18px 24px',
                        background: isExpanded ? '#fafafa' : '#ffffff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        userSelect: 'none',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, pr: '16px' }}>
                        <span
                          style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            background: '#f3e8ff',
                            color: '#65597b',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: '800',
                            fontSize: '12px',
                            flexShrink: 0,
                          }}
                        >
                          Q{t.turn_id}
                        </span>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#111827', margin: 0, flex: 1 }}>
                          {t.question_text}
                        </h3>
                      </div>

                      {/* Header Score Badges */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b' }}>
                          Tech: {t.technical_score}/10
                        </span>
                        <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', background: '#e0f2fe', color: '#0369a1' }}>
                          Vocal: {t.vocal_confidence_score}/10
                        </span>
                        <div style={{ color: '#6b7280' }}>
                          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </div>
                      </div>
                    </div>

                    {/* Expanded Body */}
                    {isExpanded && (
                      <div
                        style={{
                          padding: '20px 24px 24px 24px',
                          borderTop: '1px solid #f3f4f6',
                          background: '#ffffff',
                        }}
                      >
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                            gap: '20px',
                          }}
                        >
                          {/* Left Column: Dual Transcripts */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                            {/* Candidate Live STT Transcript */}
                            <div style={{ background: '#fafafa', borderRadius: '12px', padding: '16px', border: '1px solid #f3f4f6' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '12px', fontWeight: '700', color: '#6b7280' }}>
                                <Mic size={14} />
                                <span>Candidate Live Answer (STT)</span>
                              </div>
                              <p style={{ fontSize: '13px', fontStyle: 'italic', color: '#374151', margin: 0, lineHeight: '1.6' }}>
                                "{t.candidate_transcript || 'No candidate response recorded for this turn.'}"
                              </p>
                            </div>

                            {/* Gemini Verified Clean Transcript */}
                            {t.gemini_verified_transcript && t.gemini_verified_transcript !== t.candidate_transcript && (
                              <div style={{ background: '#f0fdf4', borderRadius: '12px', padding: '16px', border: '1px solid #bbf7d0' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '12px', fontWeight: '700', color: '#15803d' }}>
                                  <CheckCircle2 size={14} />
                                  <span>Gemini Verified Audio Transcript</span>
                                </div>
                                <p style={{ fontSize: '13px', color: '#166534', margin: 0, lineHeight: '1.6' }}>
                                  "{t.gemini_verified_transcript}"
                                </p>
                              </div>
                            )}
                          </div>

                          {/* Right Column: Eva's Assessment */}
                          <div style={{ background: '#fafafa', borderRadius: '12px', padding: '16px', border: '1px solid #f3f4f6' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '12px', fontWeight: '700', color: '#65597b' }}>
                              <Sparkles size={14} />
                              <span>Eva's Turn Assessment</span>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                              {/* Audio notes */}
                              {t.audio_notes && (
                                <div style={{ fontSize: '13px', color: '#374151', lineHeight: '1.5' }}>
                                  <strong>Delivery & Tone:</strong> {t.audio_notes}
                                </div>
                              )}

                              {/* Missing concepts */}
                              {t.missing_concepts && t.missing_concepts.length > 0 && (
                                <div>
                                  <div style={{ fontSize: '12px', fontWeight: '700', color: '#dc2626', marginBottom: '6px' }}>
                                    Missing Key Concepts:
                                  </div>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                    {t.missing_concepts.map((concept, cIdx) => (
                                      <span key={cIdx} style={{ fontSize: '11px', fontWeight: '600', background: '#fee2e2', color: '#991b1b', padding: '3px 8px', borderRadius: '9999px' }}>
                                        {concept}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Resume verification note */}
                              {t.resume_verification_note && (
                                <div style={{ fontSize: '12px', color: '#4b5563', fontStyle: 'italic', marginTop: '4px', borderTop: '1px dashed #e5e7eb', paddingTop: '8px' }}>
                                  <strong>Resume Alignment:</strong> {t.resume_verification_note}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                No per-turn evaluation items recorded for this session.
              </div>
            )}
          </div>
        </Card>

        {/* NEXT STEPS & NAVIGATION ACTION CARD */}
        <Card
          style={{
            marginTop: '28px',
            padding: '28px 36px',
            background: 'linear-gradient(135deg, #ffffff 0%, #faf8ff 100%)',
            borderRadius: '24px',
            border: '1px solid rgba(101, 89, 123, 0.15)',
            boxShadow: '0 12px 36px rgba(101, 89, 123, 0.06)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: '#ede6f8', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#65597b' }}>
              <Sparkles size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: '17px', fontWeight: '800', color: '#111827', margin: '0 0 4px 0' }}>
                Ready for your next mock session?
              </h3>
              <p style={{ fontSize: '13px', color: '#6b7280', margin: 0 }}>
                Practice another track or review your historical performance trends.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => navigate('/analytics')}
              style={{
                padding: '10px 18px',
                borderRadius: '12px',
                border: '1px solid #d1d5db',
                background: '#ffffff',
                color: '#374151',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              View Analytics
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                padding: '10px 18px',
                borderRadius: '12px',
                border: '1px solid #d1d5db',
                background: '#ffffff',
                color: '#374151',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/setup')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 22px',
                borderRadius: '12px',
                border: 'none',
                background: '#65597b',
                color: '#ffffff',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(101, 89, 123, 0.25)',
              }}
            >
              <span>Start New Session</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Report;
