import React from 'react';
import { HelpCircle, Layers, Award } from 'lucide-react';

/**
 * QuestionBankTab — Displays the 15 generated interview questions from stage 2 pipeline.
 *
 * @param {Array} questions - Array of question objects from question_tree artifact
 */
export const QuestionBankTab = ({ questions = [] }) => {
  if (!questions || questions.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--on-surface-variant)' }}>
        <HelpCircle size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
        <p style={{ fontSize: '14px', fontWeight: 600 }}>No question tree generated yet.</p>
        <p style={{ fontSize: '13px', marginTop: '4px' }}>
          Launch the track analysis to build your 15-question adaptive interview tree.
        </p>
      </div>
    );
  }

  const getDifficultyBadgeColor = (diff = '') => {
    const d = String(diff).toLowerCase();
    if (d.includes('easy') || d.includes('junior')) return { bg: '#dcfce7', color: '#15803d' };
    if (d.includes('hard') || d.includes('senior')) return { bg: '#ffe4e6', color: '#be123c' };
    return { bg: '#e0f2fe', color: '#0369a1' }; // Medium / default
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} color="var(--primary)" />
          <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--on-surface)' }}>
            Generated 15-Question Adaptive Tree
          </span>
        </div>
        <span
          style={{
            fontSize: '12px',
            fontWeight: '700',
            padding: '4px 10px',
            borderRadius: '9999px',
            background: 'var(--primary-container)',
            color: 'var(--on-primary-container)',
          }}
        >
          {questions.length} Questions
        </span>
      </div>

      <div style={{ maxHeight: '420px', overflowY: 'auto', paddingRight: '4px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {questions.map((q, idx) => {
          const qNumber = idx + 1;
          const qTopic = q.topic || q.category || q.domain || 'Technical Core';
          const qText = q.question || q.question_text || q.text || q.prompt || 'Question text not available.';
          const qDifficulty = q.difficulty || q.level || 'Medium';
          const diffColors = getDifficultyBadgeColor(qDifficulty);

          return (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.85)',
                border: '1.5px solid rgba(101, 89, 123, 0.12)',
                borderRadius: '14px',
                padding: '14px 16px',
                display: 'flex',
                gap: '14px',
                alignItems: 'flex-start',
                transition: 'border-color 180ms ease, box-shadow 180ms ease',
              }}
            >
              {/* Question Number Badge */}
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '10px',
                  background: 'rgba(101, 89, 123, 0.1)',
                  color: 'var(--primary)',
                  fontWeight: '700',
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '2px',
                }}
              >
                Q{qNumber}
              </div>

              {/* Body */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '6px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      background: 'rgba(101, 89, 123, 0.08)',
                      color: 'var(--primary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    {qTopic}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      background: diffColors.bg,
                      color: diffColors.color,
                    }}
                  >
                    {qDifficulty}
                  </span>
                </div>

                <p style={{ fontSize: '13.5px', fontWeight: '600', color: 'var(--on-surface)', margin: 0, lineHeight: '1.45' }}>
                  {qText}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default QuestionBankTab;
