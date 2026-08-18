import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { ArrowRight, RotateCcw, FileText, Sparkles, Play, Mic } from 'lucide-react';

export const LastSessionCard = ({
  sessionNumber,
  sessionTitle,
  scorePct,
  status,
  onRetake,
  onViewReport,
  lastSession,
}) => {
  const navigate = useNavigate();

  // If lastSession prop object is passed, extract values
  const currentSess = lastSession || (sessionNumber ? { number: sessionNumber, title: sessionTitle, score: scorePct, status } : null);

  if (!currentSess) {
    return (
      <Card
        className="animate-entrance animate-delay-2"
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          minHeight: '260px',
          background: 'rgba(255, 255, 255, 0.9)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Mic size={18} color="var(--primary)" />
            <h2 className="text-headline-lg" style={{ fontSize: '18px' }}>
              Last Interview Session
            </h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--on-surface-variant)', lineHeight: 1.5, margin: '8px 0 16px 0' }}>
            No sessions completed yet. Start your first 15-question technical mock interview or practice with a custom job description.
          </p>
        </div>

        <div
          style={{
            background: '#f8f6fc',
            borderRadius: 'var(--radius-lg)',
            padding: '16px',
            border: '1px border #ede6f8',
            textAlign: 'center',
            marginBottom: '16px',
          }}
        >
          <Sparkles size={20} color="#65597b" style={{ marginBottom: '6px' }} />
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--on-surface)' }}>
            Ready for your first session?
          </div>
          <div style={{ fontSize: '12px', color: 'var(--on-surface-variant)', marginTop: '2px' }}>
            Build your personalized practice track now
          </div>
        </div>

        <button
          onClick={() => navigate('/setup')}
          className="btn btn-primary"
          style={{
            width: '100%',
            borderRadius: 'var(--radius-full)',
            fontSize: '14px',
            fontWeight: 700,
          }}
        >
          <Play size={16} fill="#ffffff" />
          <span>Launch First Practice Track</span>
        </button>
      </Card>
    );
  }

  const isCompleted = (currentSess.status || '').toLowerCase() === 'completed';

  return (
    <Card className="animate-entrance animate-delay-2" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '260px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Mic size={18} color="var(--primary)" />
          <h2 className="text-headline-lg" style={{ fontSize: '18px' }}>
            Last Interview Session
          </h2>
        </div>
        <Badge variant={isCompleted ? 'completed' : 'pending'}>
          {currentSess.status || 'Active'}
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
              SESSION #{currentSess.number || 1}
            </div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--on-surface)', marginTop: '2px' }}>
              {currentSess.title}
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div className="text-label-xs" style={{ fontSize: '10px', color: 'var(--on-surface-variant)' }}>
            SCORE
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--on-surface)' }}>
            {currentSess.score || 0}%
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
