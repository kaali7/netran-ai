import React from 'react';
import StatCard from '../ui/StatCard';
import { TrendingUp, Flame, Award, Target } from 'lucide-react';

export const StatsRow = ({
  readinessPct = 84,
  streakDays = 5,
  strongestSkills = 'React & APIs',
  strongestSubtitle = 'Consistently scoring above 90%',
  needsFocusSkill = 'System Design',
  needsFocusSubtitle = 'Suggested: Review caching strategies',
  loading = false,
}) => {
  return (
    <section className="stats-grid-row animate-entrance animate-delay-1">
      {/* 1. Overall Readiness */}
      <StatCard
        type="readiness"
        title="OVERALL READINESS"
        value={`${readinessPct}%`}
        progress={readinessPct}
        icon={TrendingUp}
        loading={loading}
      />

      {/* 2. Practice Streak */}
      <StatCard
        type="streak"
        title="PRACTICE STREAK"
        value={`${streakDays} Days`}
        subtitle="Keep it up! Consistency is key."
        icon={Flame}
        loading={loading}
      />

      {/* 3. Strongest Skills */}
      <StatCard
        type="strong"
        title="STRONGEST SKILLS"
        value={strongestSkills}
        subtitle={strongestSubtitle}
        icon={Award}
        loading={loading}
      />

      {/* 4. Needs Focus */}
      <StatCard
        type="focus"
        title="NEEDS FOCUS"
        value={needsFocusSkill}
        subtitle={needsFocusSubtitle}
        icon={Target}
        loading={loading}
      />
    </section>
  );
};

export default StatsRow;
