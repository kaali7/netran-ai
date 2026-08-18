import React, { useState } from 'react';
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
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

export const Report = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();

  // Accordion open/close state for question breakdowns
  const [expandedQuestions, setExpandedQuestions] = useState({
    0: true, // Q1 open by default
    1: false,
    2: false,
  });

  const toggleQuestion = (index) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const questionData = [
    {
      id: 'Q1',
      question: 'How would you handle cache invalidation in a distributed system?',
      yourAnswer:
        '"I would use a combination of TTL and event-driven invalidation. For consistency, maybe a consensus algorithm like Raft..."',
      positiveFeedback: 'Great mention of Raft for maintaining consensus across nodes.',
      improvementFeedback:
        'Missed network partition handling strategies which is crucial for distributed caches.',
    },
    {
      id: 'Q2',
      question: 'Design a rate limiter for a public API.',
      yourAnswer:
        '"I would implement a Token Bucket or Leaky Bucket algorithm backed by Redis. Using sliding window logs helps prevent traffic spikes near boundary thresholds..."',
      positiveFeedback:
        'Excellent choice of Token Bucket algorithm with Redis for low latency enforcement.',
      improvementFeedback:
        'Consider detailing fallback strategies when Redis experiences a connection timeout.',
    },
    {
      id: 'Q3',
      question:
        'What strategies do you employ to prevent race conditions when handling simultaneous DB writes in Node.js?',
      yourAnswer:
        '"Using database transactions with pessimistic locking or optimistic concurrency control using version timestamps..."',
      positiveFeedback:
        'Strong understanding of ACID properties and optimistic locking mechanisms.',
      improvementFeedback:
        'Could elaborate further on queue-based message brokers (e.g. RabbitMQ/Kafka) for write serialization.',
    },
  ];

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px' }}>
      {/* Top Navigation Header */}
      <header
        style={{
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--color-outline-variant)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: '16px 24px',
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
          {/* Netran AI Brand Title */}
          <div
            onClick={() => navigate('/dashboard')}
            style={{
              cursor: 'pointer',
              fontWeight: '800',
              fontSize: '20px',
              color: 'var(--color-primary)',
              letterSpacing: '-0.02em',
            }}
          >
            Netran AI
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
                color: 'var(--color-on-surface-variant)',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              <ArrowLeft size={16} />
              <span>Back to Dashboard</span>
            </button>

            {/* Profile Avatar */}
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: '#e0e7ff',
                color: '#4f46e5',
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

      {/* Main Container */}
      <div style={{ maxWidth: '1200px', margin: '32px auto 0 auto', padding: '0 24px' }}>
        
        {/* SESSION SUMMARY BANNER CARD */}
        <Card
          style={{
            marginBottom: '24px',
            padding: '28px 32px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.03)',
          }}
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h1
                  style={{
                    fontSize: '26px',
                    fontWeight: '800',
                    color: '#111827',
                    letterSpacing: '-0.02em',
                    margin: 0,
                  }}
                >
                  Session Summary: Fullstack Practice Track
                </h1>
                <span style={{ fontSize: '24px' }}>🎯</span>
              </div>

              {/* Session Meta Infos */}
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
                  <span>Interviewed by Eva</span>
                </div>
                <span>•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={15} />
                  <span>Completed on Aug 9, 2026</span>
                </div>
                <span>•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={15} />
                  <span>Duration: 18m 42s</span>
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
                  background: '#c3ecd2',
                  color: '#1e4620',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <RotateCcw size={15} />
                <span>Retake Session</span>
              </button>

              <button
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
                <BarChart2 size={15} />
                <span>Improve Weak Areas</span>
              </button>

              <button
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
                <span>Share</span>
              </button>
            </div>
          </div>
        </Card>

        {/* TOP ROW GRID (Overall Readiness & Skill Matrix) */}
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
              borderRadius: '20px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#111827', margin: '0 0 20px 0' }}>
              Overall Readiness
            </h2>

            {/* Circular Donut Gauge */}
            <div style={{ position: 'relative', width: '160px', height: '160px', margin: '0 auto 16px auto' }}>
              <svg width="160" height="160" viewBox="0 0 160 160">
                {/* Background Ring */}
                <circle
                  cx="80"
                  cy="80"
                  r="62"
                  fill="none"
                  stroke="#f3f4f6"
                  strokeWidth="14"
                />
                {/* Active Progress Arc (82%) */}
                <circle
                  cx="80"
                  cy="80"
                  r="62"
                  fill="none"
                  stroke="#5b4a78"
                  strokeWidth="14"
                  strokeDasharray={2 * Math.PI * 62}
                  strokeDashoffset={2 * Math.PI * 62 * (1 - 0.82)}
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
                  82
                </span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#6b7280', marginTop: '2px' }}>
                  / 100
                </span>
              </div>
            </div>

            {/* Readiness Badge Chip */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: '#e6f4ea',
                color: '#137333',
                padding: '6px 16px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: '700',
                marginBottom: '24px',
              }}
            >
              <CheckCircle2 size={14} />
              <span>Mid-Level Ready</span>
            </div>

            {/* Voice Performance Sub-Card */}
            <div
              style={{
                width: '100%',
                background: '#f9fafb',
                borderRadius: '12px',
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
                Voice Performance
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#374151', fontSize: '13px', fontWeight: '500' }}>
                    <Zap size={14} style={{ color: '#6b7280' }} />
                    <span>Pace</span>
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: '#15803d' }}>
                    135 WPM (Optimal)
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#374151', fontSize: '13px', fontWeight: '500' }}>
                    <Mic size={14} style={{ color: '#6b7280' }} />
                    <span>Filler Words</span>
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: '#15803d' }}>
                    3 (Excellent)
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
              borderRadius: '20px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#111827', margin: '0 0 24px 0' }}>
                Skill Breakdown Matrix
              </h2>

              {/* Skill Bars */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {/* Skill 1 */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                    <span>System Architecture</span>
                    <span style={{ fontWeight: '700' }}>88%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '88%', height: '100%', background: '#5b4a78', borderRadius: '9999px' }} />
                  </div>
                </div>

                {/* Skill 2 */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                    <span>Technical Accuracy</span>
                    <span style={{ fontWeight: '700' }}>80%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '80%', height: '100%', background: '#5b4a78', borderRadius: '9999px' }} />
                  </div>
                </div>

                {/* Skill 3 */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                    <span>Communication Clarity</span>
                    <span style={{ fontWeight: '700' }}>85%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '85%', height: '100%', background: '#5b4a78', borderRadius: '9999px' }} />
                  </div>
                </div>

                {/* Skill 4 */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                    <span>Problem Solving Speed</span>
                    <span style={{ fontWeight: '700', color: '#15803d' }}>75%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: '75%', height: '100%', background: '#426651', borderRadius: '9999px' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* AI Feedback Box */}
            <div
              style={{
                marginTop: '24px',
                background: '#f5f0fb',
                borderRadius: '14px',
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
                  AI Feedback
                </div>
                <p style={{ fontSize: '13px', color: '#49454d', margin: 0, lineHeight: '1.5' }}>
                  Strong architectural clarity; work on caching edge cases to improve problem-solving speed in complex scenarios.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* BOTTOM SECTION (Question-by-Question Breakdown) */}
        <Card
          style={{
            padding: '28px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <MessageSquare size={18} style={{ color: '#65597b' }} />
            <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#374151', letterSpacing: '0.04em', margin: 0, textTransform: 'uppercase' }}>
              Question-By-Question Breakdown With Eva
            </h2>
          </div>

          {/* Question Accordion List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {questionData.map((q, idx) => {
              const isExpanded = expandedQuestions[idx];

              return (
                <div
                  key={q.id}
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', pr: '16px' }}>
                      <span
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          background: '#f3e8ff',
                          color: '#65597b',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: '700',
                          fontSize: '12px',
                          flexShrink: 0,
                        }}
                      >
                        {q.id}
                      </span>
                      <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#111827', margin: 0 }}>
                        {q.question}
                      </h3>
                    </div>

                    <div style={{ color: '#6b7280' }}>
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
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
                        {/* Your Answer Sub-Card */}
                        <div
                          style={{
                            background: '#fafafa',
                            borderRadius: '12px',
                            padding: '16px 20px',
                            border: '1px solid #f3f4f6',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', fontSize: '12px', fontWeight: '700', color: '#6b7280' }}>
                            <User size={14} />
                            <span>Your Answer</span>
                          </div>
                          <p
                            style={{
                              fontSize: '13px',
                              fontStyle: 'italic',
                              color: '#374151',
                              margin: 0,
                              lineHeight: '1.6',
                            }}
                          >
                            {q.yourAnswer}
                          </p>
                        </div>

                        {/* Eva's Assessment Sub-Card */}
                        <div
                          style={{
                            background: '#fafafa',
                            borderRadius: '12px',
                            padding: '16px 20px',
                            border: '1px solid #f3f4f6',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '12px', fontWeight: '700', color: '#6b7280' }}>
                            <Sparkles size={14} style={{ color: '#65597b' }} />
                            <span>Eva's Assessment</span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {/* Positive feedback */}
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                              <CheckCircle2 size={16} style={{ color: '#16a34a', flexShrink: 0, marginTop: '2px' }} />
                              <span style={{ fontSize: '13px', color: '#1f2937', lineHeight: '1.5' }}>
                                {q.positiveFeedback}
                              </span>
                            </div>

                            {/* Improvement feedback */}
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                              <AlertTriangle size={16} style={{ color: '#dc2626', flexShrink: 0, marginTop: '2px' }} />
                              <span style={{ fontSize: '13px', color: '#1f2937', lineHeight: '1.5' }}>
                                {q.improvementFeedback}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Report;
