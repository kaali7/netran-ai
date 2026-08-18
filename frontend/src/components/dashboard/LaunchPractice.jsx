import React from 'react';
import Card from '../ui/Card';
import { Mic, FileText, Rocket } from 'lucide-react';

/**
 * LaunchPractice card — two CTAs:
 * 1. "Start Full 15-Q Mock" → opens TemplatePicker modal (no JD/resume required)
 * 2. "Practice Custom JD & RESUME" → navigates to /setup for full pipeline
 */
export const LaunchPractice = ({ onStartFullMock, onPracticeCustomJD }) => {
  return (
    <Card className="animate-entrance animate-delay-2" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '260px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Rocket size={20} color="var(--primary)" />
          <h2 className="text-headline-lg" style={{ fontSize: '20px' }}>
            Launch Practice
          </h2>
        </div>
        <p className="text-body-md" style={{ fontSize: '14px', marginTop: '4px' }}>
          Start a new session to improve your readiness score.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '24px' }}>
        {/* Primary CTA — opens TemplatePicker modal */}
        <button
          id="launch-practice-template-mock"
          onClick={onStartFullMock}
          className="btn btn-primary"
          style={{
            width: '100%',
            padding: '14px 20px',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
          }}
        >
          <Mic size={16} strokeWidth={2.4} />
          <span>Start Full 15-Q Mock</span>
        </button>

        {/* Secondary CTA — custom JD & resume pipeline */}
        <button
          id="launch-practice-custom-jd"
          onClick={onPracticeCustomJD}
          className="btn btn-ghost"
          style={{
            width: '100%',
            padding: '14px 20px',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
          }}
        >
          <FileText size={16} strokeWidth={2.2} />
          <span>Practice Custom JD &amp; RESUME</span>
        </button>
      </div>
    </Card>
  );
};

export default LaunchPractice;
