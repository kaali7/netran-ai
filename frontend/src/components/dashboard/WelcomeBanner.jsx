import React from 'react';
import { TrendingUp } from 'lucide-react';

export const WelcomeBanner = ({
  candidateName = 'Arjun',
  readinessPct = 84,
  targetRole = 'Mid-Level Fullstack',
}) => {
  return (
    <section className="welcome-banner animate-entrance">
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h1 className="text-headline-xl">Welcome back, {candidateName}</h1>
          <span style={{ fontSize: '26px' }}>👋</span>
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
