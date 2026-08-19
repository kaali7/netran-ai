import api from './api';

/**
 * Fetch candidate session history archives from backend with filter criteria.
 * 
 * @param {Object} filters - Filter criteria: { statusFilter, search, dateFilter, trackFilter }
 */
export async function getHistorySessions(filters = {}, customOpts = {}) {
  const params = new URLSearchParams();
  if (filters.statusFilter) params.append('status_filter', filters.statusFilter);
  if (filters.search) params.append('search', filters.search);
  if (filters.dateFilter) params.append('date_filter', filters.dateFilter);
  if (filters.trackFilter) params.append('track_filter', filters.trackFilter);

  if (filters.dateFilter === 'custom') {
    if (customOpts.customDays) params.append('custom_days', customOpts.customDays);
    if (customOpts.startDate) params.append('start_date', customOpts.startDate);
    if (customOpts.endDate) params.append('end_date', customOpts.endDate);
  }

  const response = await api.get(`/history/sessions?${params.toString()}`);
  return response.data;
}

/**
 * Fetch comprehensive session detail payload including question tree & resume analysis.
 * 
 * @param {string} sessionId 
 */
export async function getHistorySessionDetail(sessionId) {
  const response = await api.get(`/history/detail/${sessionId}`);
  return response.data;
}

/**
 * Export candidate session history array as a CSV download.
 * 
 * @param {Array} sessions 
 */
export function exportHistoryCSV(sessions = []) {
  if (!sessions || sessions.length === 0) {
    alert('No history records available to export.');
    return;
  }

  const headers = ['Session ID', 'Date', 'Track / Role', 'Company', 'Status', 'Score', 'Hiring Signal', 'Total Questions'];
  const rows = sessions.map((s) => [
    s.id,
    s.dateText || s.created_at,
    `"${s.role_title || s.track}"`,
    `"${s.company || 'Tech Corporation'}"`,
    s.status,
    s.score ? `${s.score}/100` : 'N/A',
    s.hiring_signal || 'Pending',
    s.total_questions || 15,
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `netran_interview_history_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
