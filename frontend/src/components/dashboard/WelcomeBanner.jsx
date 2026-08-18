import React from 'react';
import { TrendingUp, Sparkles } from 'lucide-react';

export const WelcomeBanner = ({
  candidateName = 'Arjun',
  readinessPct = 84,
  targetRole = 'Mid-Level Fullstack',
}) => {
  return (
    <section className="welcome-banner animate-entrance">
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h1 className="text-headline-xl">Welcome back, {candidateName}</h1>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(101, 89, 123, 0.12)',
            }}
          >
            <Sparkles size={18} color="var(--primary)" />
          </div>
        </div>
        <p className="text-body-md" style={{ marginTop: '4px' }}>
          Ready to ace your next technical interview?
        </p>
      </div>

      <div className="readiness-capsule">
        <div className="readiness-icon-circle">
          <TrendingUp size={20} strokeWidth={2.5} />
        </div>
        <div>
          <div className="text-label-xs" style={{ color: 'var(--primary)', marginBottom: '2px' }}>
            READINESS SCORE
          </div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--on-surface)' }}>
            You're {readinessPct}% ready for {targetRole} interviews.
          </div>
        </div>
      </div>
    </section>
  );
};

export default WelcomeBanner;

