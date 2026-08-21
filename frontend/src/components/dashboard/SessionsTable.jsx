import React from 'react';
import Card from '../ui/Card';
import { Plus, FileText, Clock, Calendar, Layers, RotateCw, Play, Sparkles } from 'lucide-react';

export const SessionsTable = ({
  sessions = [],
  onNewWorkspace,
  onViewFeedback,
}) => {
  const renderActionButton = (session) => {
    if (session.status === 'in_progress') {
      return (
        <button
          onClick={() => onViewFeedback && onViewFeedback(session)}
          className="btn"
          style={{
            padding: '8px 18px',
            fontSize: '13px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--primary)',
            color: '#ffffff',
            fontWeight: 700,
            whiteSpace: 'nowrap',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            border: 'none',
          }}
        >
          <RotateCw size={13} />
          <span>Resume Practice</span>
        </button>
      );
    }

    if (session.status === 'ready') {
      return (
        <button
          onClick={() => onViewFeedback && onViewFeedback(session)}
          className="btn"
          style={{
            padding: '8px 18px',
            fontSize: '13px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--primary)',
            color: '#ffffff',
            fontWeight: 700,
            whiteSpace: 'nowrap',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            border: 'none',
          }}
        >
          <Play size={13} />
          <span>Start Practice</span>
        </button>
      );
    }

    if (session.status === 'evaluating' && !session.hasReport) {
      return (
        <button
          onClick={() => onViewFeedback && onViewFeedback(session)}
          className="btn"
          style={{
            padding: '8px 18px',
            fontSize: '13px',
            borderRadius: 'var(--radius-full)',
            background: '#d97706',
            color: '#ffffff',
            fontWeight: 700,
            whiteSpace: 'nowrap',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            border: 'none',
          }}
        >
          <Sparkles size={13} />
          <span>Complete Eval</span>
        </button>
      );
    }

    return (
      <button
        onClick={() => onViewFeedback && onViewFeedback(session)}
        className="btn btn-ghost"
        style={{
          padding: '8px 18px',
          fontSize: '13px',
          borderRadius: 'var(--radius-full)',
          borderColor: '#d1d3d6',
          color: 'var(--on-surface)',
          fontWeight: 600,
          whiteSpace: 'nowrap',
        }}
      >
        View Feedback
      </button>
    );
  };

  return (
    <Card className="animate-entrance animate-delay-3 sessions-table-card" style={{ padding: '24px 28px' }}>
      {/* Header with Title and + New Workspace Button */}
      <div
        className="sessions-table-header"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={20} style={{ color: 'var(--primary)' }} />
          <h2 className="text-headline-lg sessions-table-title">
            Recent Practice Sessions & Feedback
          </h2>
        </div>

        <button
          onClick={onNewWorkspace}
          className="btn new-workspace-btn"
        >
          <Plus size={15} strokeWidth={2.4} />
          <span>New Workspace</span>
        </button>
      </div>

      {/* Sessions List or Empty State */}
      {sessions.length === 0 ? (
        <div
          style={{
            background: '#ffffff',
            borderRadius: 'var(--radius-lg)',
            padding: '36px 24px',
            textAlign: 'center',
            border: '1px solid #f0f1f2',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: '#f3f0f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)',
              marginBottom: '12px',
            }}
          >
            <Layers size={22} />
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--on-surface)' }}>
            No Historical Sessions Found
          </div>
          <p
            style={{
              fontSize: '13px',
              color: 'var(--on-surface-variant)',
              marginTop: '4px',
              maxWidth: '420px',
            }}
          >
            Start your first practice track to build your technical readiness score, track session transcripts, and receive multimodal AI feedback.
          </p>
        </div>
      ) : (
        <div>
          {sessions.map((session) => (
            <div key={session.id} className="session-row-card">
              {/* Left: Icon and Title/Date */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div className={session.isPrimaryIcon ? 'session-icon-box' : 'session-icon-box-muted'}>
                  <FileText size={20} />
                </div>
                <div>
                  <div className="session-title-text">
                    Session #{session.number}: {session.title}
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '12px',
                      color: 'var(--on-surface-variant)',
                      marginTop: '2px',
                    }}
                  >
                    {session.dateType === 'clock' ? <Clock size={12} /> : <Calendar size={12} />}
                    <span>{session.dateText}</span>
                  </div>
                </div>
              </div>

              {/* Right: Score and Contextual CTA */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                <div style={{ textAlign: 'right' }}>
                  <div className="text-label-xs" style={{ fontSize: '10px', color: 'var(--on-surface-variant)' }}>
                    SCORE
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--on-surface)' }}>
                    {session.score || 0}%
                  </div>
                </div>

                {renderActionButton(session)}
              </div>
            </div>
          ))}
        </div>
      )}

    </Card>
  );
};

export default SessionsTable;
