import React from 'react';
import Card from '../ui/Card';
import { Plus, FileText, Clock, Calendar, Layers } from 'lucide-react';

export const SessionsTable = ({
  sessions = [],
  onNewWorkspace,
  onViewFeedback,
}) => {
  return (
    <Card className="animate-entrance animate-delay-3" style={{ padding: '28px 32px' }}>
      {/* Header with Title and + New Workspace Button */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '20px' }}>📜</span>
          <h2 className="text-headline-lg" style={{ fontSize: '20px' }}>
            Recent Practice Sessions & Feedback
          </h2>
        </div>

        <button
          onClick={onNewWorkspace}
          className="btn"
          style={{
            background: 'var(--primary)',
            color: '#ffffff',
            padding: '10px 18px',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            borderRadius: 'var(--radius-full)',
          }}
        >
          <Plus size={16} strokeWidth={2.4} />
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
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--on-surface)' }}>
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

              {/* Right: Score and View Feedback CTA */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                <div style={{ textAlign: 'right' }}>
                  <div className="text-label-xs" style={{ fontSize: '10px', color: 'var(--on-surface-variant)' }}>
                    SCORE
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--on-surface)' }}>
                    {session.score || 0}%
                  </div>
                </div>

                <button
                  onClick={() => onViewFeedback && onViewFeedback(session.id)}
                  className="btn btn-ghost"
                  style={{
                    padding: '8px 18px',
                    fontSize: '13px',
                    borderRadius: 'var(--radius-full)',
                    borderColor: '#d1d3d6',
                    color: 'var(--on-surface)',
                    fontWeight: 600,
                  }}
                >
                  View Feedback
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

export default SessionsTable;
