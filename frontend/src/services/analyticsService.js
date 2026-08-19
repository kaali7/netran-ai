import api from './api';

/**
 * Fetch candidate session history and aggregate analytics data over the given time window.
 * 
 * @param {string} timeRange - Filter window: '30d' | '90d' | 'all'
 */
export async function getAggregatedAnalytics(timeRange = '30d', customOptions = {}) {
  try {
    const params = new URLSearchParams({ time_range: timeRange });
    if (timeRange === 'custom') {
      if (customOptions.customDays) params.append('custom_days', customOptions.customDays);
      if (customOptions.startDate) params.append('start_date', customOptions.startDate);
      if (customOptions.endDate) params.append('end_date', customOptions.endDate);
    }

    // Fetch real-time candidate analytics summary from backend API
    const response = await api.get(`/analytics/summary?${params.toString()}`);
    const data = response.data;

    return {
      timeRange: data.time_range || timeRange,
      compositeScore: data.composite_score ?? 0,
      totalSessions: data.total_sessions ?? 0,
      trendPercent: data.trend_percent ?? 0,
      strongestArea: data.strongest_area || 'System Architecture & Problem Solving',
      insights: data.insights || [],
      skillMatrix: (data.skill_matrix || []).map((s) => ({
        name: s.name,
        score: s.score,
        color: s.color || '#65597b',
      })),
      sessionComparison: (data.session_comparison || []).map((sc) => ({
        label: sc.label,
        score: sc.score,
        active: sc.active,
      })),
    };
  } catch (err) {
    console.warn('Backend analytics fetch error, returning fallback onboarding analytics:', err);
    return {
      timeRange,
      compositeScore: 0,
      totalSessions: 0,
      trendPercent: 0,
      strongestArea: 'N/A - Complete practice track',
      insights: [
        {
          id: 1,
          type: 'positive',
          text: 'Welcome to Netran AI! Complete your first mock interview practice track to unlock real-time performance analytics.',
        },
        {
          id: 2,
          type: 'warning',
          text: 'No completed practice sessions found. Launch an interview session from the Dashboard to build your tech skill matrix.',
        },
      ],
      skillMatrix: [
        { name: 'System Architecture', score: 0, color: '#65597b' },
        { name: 'Communication & Pacing', score: 0, color: '#65597b' },
        { name: 'Problem Solving & Tradeoffs', score: 0, color: '#65597b' },
        { name: 'Code Quality & Professionalism', score: 0, color: '#65597b' },
      ],
      sessionComparison: [
        { label: 'S1', score: 0, active: false },
        { label: 'S2', score: 0, active: false },
        { label: 'S3', score: 0, active: false },
        { label: 'S4', score: 0, active: false },
        { label: 'S5', score: 0, active: true },
      ],
    };
  }
}

