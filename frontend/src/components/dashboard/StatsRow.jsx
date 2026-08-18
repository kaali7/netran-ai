import React from 'react';
import StatCard from '../ui/StatCard';

export const StatsRow = ({
  readinessPct = 84,
  streakDays = 5,
  strongestSkills = 'React & APIs',
  strongestSubtitle = 'Consistently scoring above 90%',
  needsFocusSkill = 'System Design',
  needsFocusSubtitle = 'Suggested: Review caching strategies',
}) => {
  return (
    <section className="stats-grid-row animate-entrance animate-delay-1">
      {/* 1. Overall Readiness */}
      <StatCard
        type="readiness"
        title="OVERALL READINESS"
        value={`${readinessPct}%`}
        progress={readinessPct}
      />

      {/* 2. Practice Streak */}
      <StatCard
        type="streak"
        title="PRACTICE STREAK"
        value={`${streakDays} Days`}
        subtitle="Keep it up! Consistency is key."
      />

      {/* 3. Strongest Skills */}
      <StatCard
        type="strong"
        title="STRONGEST SKILLS"
        value={strongestSkills}
        subtitle={strongestSubtitle}
      />

      {/* 4. Needs Focus */}
      <StatCard
        type="focus"
        title="NEEDS FOCUS"
        value={needsFocusSkill}
        subtitle={needsFocusSubtitle}
      />
    </section>
  );
};

export default StatsRow;
