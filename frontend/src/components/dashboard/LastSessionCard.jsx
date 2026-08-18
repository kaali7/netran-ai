import React from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { ArrowRight, RotateCcw, FileText } from 'lucide-react';

export const LastSessionCard = ({
  sessionNumber = 14,
  sessionTitle = 'Backend Caching',
  scorePct = 88,
  status = 'Completed',
  onRetake,
  onViewReport,
}) => {
  return (
    <Card className="animate-entrance animate-delay-2" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '260px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🎙️</span>
          <h2 className="text-headline-lg" style={{ fontSize: '18px' }}>
            Last Interview Session
          </h2>
        </div>
        <Badge variant={status.toLowerCase() === 'completed' ? 'completed' : 'pending'}>
          {status}
        </Badge>
      </div>

      {/* Middle Session Summary Pill Box */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          padding: '14px 18px',
          border: '1px solid #f0f1f2',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          margin: '18px 0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div className="session-icon-box">
            <FileText size={20} strokeWidth={2.2} />
          </div>
          <div>
            <div className="text-label-xs" style={{ color: 'var(--on-surface-variant)', fontSize: '10px' }}>
              SESSION #{sessionNumber}
            </div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--on-surface)', marginTop: '2px' }}>
              {sessionTitle}
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="text-label-xs" style={{ fontSize: '10px', color: 'var(--on-surface-variant)' }}>
            SCORE
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--on-surface)' }}>
            {scorePct}%
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={onRetake}
          className="btn btn-secondary-action"
          style={{
            width: '100%',
            borderRadius: 'var(--radius-full)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          <RotateCcw size={16} />
          <span>Retake Session</span>
        </button>

        <button
          onClick={onViewReport}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--on-surface-variant)',
            transition: 'color 150ms ease',
            padding: '4px 8px',
          }}
          onMouseOver={(e) => (e.currentTarget.style.color = 'var(--primary)')}
          onMouseOut={(e) => (e.currentTarget.style.color = 'var(--on-surface-variant)')}
        >
          <span>View Full Report</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </Card>
  );
};

export default LastSessionCard;
