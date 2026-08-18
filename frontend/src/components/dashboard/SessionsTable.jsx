import React from 'react';
import Card from '../ui/Card';
import { Plus, FileText, Clock, Calendar } from 'lucide-react';

export const SessionsTable = ({
  sessions = [
    {
      id: 'sess-14',
      number: 14,
      title: 'Backend Caching',
      dateText: 'Yesterday',
      dateType: 'clock',
      score: 88,
      isPrimaryIcon: true,
    },
    {
      id: 'sess-13',
      number: 13,
      title: 'React State Management',
      dateText: 'Aug 5',
      dateType: 'calendar',
      score: 82,
      isPrimaryIcon: false,
    },
  ],
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

      {/* Sessions List */}
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
                  {session.score}%
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
    </Card>
  );
};

export default SessionsTable;
