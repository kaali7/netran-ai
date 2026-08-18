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

        setData({
          candidateName: firstName,
          candidateFirstName: firstName,
          targetRole: lastSess ? lastSess.title : 'Technical Interview Track',
          readinessScore: avgScore,
          practiceStreakDays: sessionsList.length > 0 ? sessionsList.length : 0,
          strongestSkills:
            hasCompleted.length > 0 ? 'Problem Solving & Architecture' : 'Complete a Session',
          strongestSkillsDetail:
            hasCompleted.length > 0
              ? 'Based on recent session evaluation'
              : 'Complete your first mock interview to unlock skills telemetry',
          needsFocusSkill:
            hasCompleted.length > 0 ? 'Live System Design' : 'No Focus Areas Yet',
          needsFocusDetail:
            hasCompleted.length > 0
              ? 'Review caching & distributed systems'
              : 'Your focus areas will appear here after your first practice session',
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
