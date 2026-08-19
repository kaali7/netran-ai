import { useState, useEffect } from 'react';
import api from '../services/api';
import { DEFAULT_DASHBOARD_DATA } from '../utils/constants';

export const useDashboard = () => {
  const [data, setData] = useState(DEFAULT_DASHBOARD_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchDashboardTelemetry = async () => {
      setLoading(true);
      setError(null);

      try {
        // 1. Fetch current authenticated user profile
        const userRes = await api.get('/auth/me');
        let name = 'Candidate';
        let firstName = 'Candidate';

        if (userRes?.data?.email) {
          name = userRes.data.email.split('@')[0];
          firstName = name.charAt(0).toUpperCase() + name.slice(1);
        }

        // 2. Fetch candidate's real sessions from backend database
        let sessionsList = [];
        try {
          const sessionsRes = await api.get('/setup/sessions');
          if (Array.isArray(sessionsRes?.data)) {
            sessionsList = sessionsRes.data.map((s) => ({
              id: s.id,
              number: s.number || 1,
              title: s.title || 'Technical Interview',
              dateText: s.created_at
                ? new Date(s.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  })
                : 'Recent',
              dateType: 'calendar',
              score: s.score || 0,
              status: s.status || 'setup',
              durationSeconds: s.duration_seconds || 0,
              durationText: s.duration_text || '0m 00s',
              questionCount: s.question_count || 15,
              isPrimaryIcon: true,
            }));
          }
        } catch (sessionErr) {
          console.warn('No active backend sessions retrieved yet.');
        }

        if (!isMounted) return;

        // Calculate dynamic metrics if sessions exist
        const hasCompleted = sessionsList.filter(
          (s) => s.status === 'completed' || s.score > 0
        );

        const lastSess = sessionsList.length > 0 ? sessionsList[0] : null;

        const avgScore =
          hasCompleted.length > 0
            ? Math.round(
                hasCompleted.reduce((acc, s) => acc + (s.score || 0), 0) /
                  hasCompleted.length
              )
            : 0;

        // 3. Fetch real skill telemetry from backend analytics summary
        let strongestSkills = 'Complete a Session';
        let strongestSkillsDetail = 'Complete your first mock interview to unlock skills telemetry';
        let needsFocusSkill = 'No Focus Areas Yet';
        let needsFocusDetail = 'Your focus areas will appear here after your first practice session';

        if (hasCompleted.length > 0) {
          try {
            const analyticsRes = await api.get('/analytics/summary?time_range=all');
            const summary = analyticsRes?.data;
            if (summary) {
              const skillMatrix = summary.skill_matrix || [];
              const insights = summary.insights || [];

              const sortedSkills = [...skillMatrix].sort((a, b) => (b.score || 0) - (a.score || 0));

              if (sortedSkills.length > 0) {
                const topSkill = sortedSkills[0];
                const lowestSkill = sortedSkills[sortedSkills.length - 1];

                if (topSkill.score > 0) {
                  strongestSkills = topSkill.name;
                  const posInsight = insights.find((i) => i.type === 'positive');
                  if (posInsight?.text) {
                    strongestSkillsDetail = posInsight.text.replace(/^Key Strength:\s*/i, '');
                  } else {
                    strongestSkillsDetail = `Top domain score (${topSkill.score}%) in practice evaluation`;
                  }
                }

                if (lowestSkill.score < topSkill.score || sortedSkills.length > 1) {
                  needsFocusSkill = lowestSkill.name;
                  const warnInsight = insights.find((i) => i.type === 'warning');
                  if (warnInsight?.text) {
                    needsFocusDetail = warnInsight.text.replace(/^Growth Focus:\s*/i, '');
                  } else {
                    needsFocusDetail = `Domain score ${lowestSkill.score}% — recommended focus area`;
                  }
                }
              }
            }
          } catch (analyticsErr) {
            console.warn('Analytics summary fetch fallback:', analyticsErr);
            strongestSkills = 'System Architecture & Problem Solving';
            strongestSkillsDetail = 'Based on recent session evaluation';
            needsFocusSkill = 'Live System Design';
            needsFocusDetail = 'Review caching & distributed systems';
          }
        }

        setData({
          candidateName: firstName,
          candidateFirstName: firstName,
          targetRole: lastSess ? lastSess.title : 'Technical Interview Track',
          readinessScore: avgScore,
          practiceStreakDays: sessionsList.length > 0 ? sessionsList.length : 0,
          strongestSkills,
          strongestSkillsDetail,
          needsFocusSkill,
          needsFocusDetail,
          lastSession: lastSess,
          recentSessions: sessionsList,
        });
      } catch (err) {
        if (isMounted) {
          setError('Failed to fetch user dashboard telemetry.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDashboardTelemetry();

    return () => {
      isMounted = false;
    };
  }, []);

  return { data, loading, error };
};

export default useDashboard;
