// Netran AI — Default Constants & Mock Telemetry

export const DEFAULT_DASHBOARD_DATA = {
  candidateName: 'Arjun Sharma',
  candidateFirstName: 'Arjun',
  targetRole: 'Mid-Level Fullstack',
  readinessScore: 84,
  practiceStreakDays: 5,
  strongestSkills: 'React & APIs',
  strongestSkillsDetail: 'Consistently scoring above 90%',
  needsFocusSkill: 'System Design',
  needsFocusDetail: 'Suggested: Review caching strategies',
  lastSession: {
    number: 14,
    title: 'Backend Caching',
    score: 88,
    status: 'Completed',
    date: 'Yesterday',
    sessionId: 'sess_default_14',
  },
  recentSessions: [
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
};
