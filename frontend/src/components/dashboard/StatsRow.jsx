import React from 'react';
import StatCard from '../ui/StatCard';
import { TrendingUp, Flame, Award, Target } from 'lucide-react';

export const StatsRow = ({
  readinessPct = 0,
  totalSessions = 0,
  completedSessions = 0,
  streakDays, // backwards compatibility fallback
  strongestSkills = 'Complete a Session',
  strongestSubtitle = 'Complete your first mock interview to unlock skills telemetry',
  strongestFullDetail = '',
  needsFocusSkill = 'No Focus Areas Yet',
  needsFocusSubtitle = 'Your focus areas will appear here after your first practice session',
  needsFocusFullDetail = '',
  loading = false,
}) => {
  const sessionCount = totalSessions || streakDays || 0;

  const readinessSubtitle =
    readinessPct > 0
      ? readinessPct >= 75
        ? 'Strong technical interview readiness'
        : readinessPct >= 50
        ? 'Steady progress across evaluations'
        : 'Score based on evaluated sessions'
      : 'Complete a mock session to gauge readiness';

  const sessionsSubtitle =
    sessionCount > 0
      ? completedSessions > 0
        ? `${completedSessions} evaluated mock ${completedSessions === 1 ? 'interview' : 'interviews'}`
        : `${sessionCount} practice ${sessionCount === 1 ? 'session' : 'sessions'} conducted`
      : 'Start your first practice session!';

  return (
    <section className="stats-grid-row animate-entrance animate-delay-1">
      {/* 1. Overall Readiness */}
      <StatCard
        type="readiness"
        title="OVERALL READINESS"
        value={`${readinessPct}%`}
        progress={readinessPct}
        subtitle={readinessSubtitle}
        icon={TrendingUp}
        loading={loading}
      />

      {/* 2. Practice Sessions */}
      <StatCard
        type="streak"
        title="PRACTICE SESSIONS"
        value={`${sessionCount} ${sessionCount === 1 ? 'Session' : 'Sessions'}`}
        subtitle={sessionsSubtitle}
        icon={Flame}
        loading={loading}
      />

      {/* 3. Strongest Skills */}
      <StatCard
        type="strong"
        title="STRONGEST SKILLS"
        value={strongestSkills}
        subtitle={strongestSubtitle}
        fullDetail={strongestFullDetail}
        icon={Award}
        loading={loading}
      />

      {/* 4. Needs Focus */}
      <StatCard
        type="focus"
        title="NEEDS FOCUS"
        value={needsFocusSkill}
        subtitle={needsFocusSubtitle}
        fullDetail={needsFocusFullDetail}
        icon={Target}
        loading={loading}
      />
    </section>
  );
};

export default StatsRow;
