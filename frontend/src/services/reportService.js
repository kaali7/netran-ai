import api from './api';

/**
 * Trigger Stage 4 multimodal evaluation background task.
 * POST /api/v1/reports/generate/{session_id}
 */
export async function triggerReportGeneration(sessionId) {
  const response = await api.post(`/reports/generate/${sessionId}`);
  return response.data;
}

/**
 * Fetch evaluation report JSON and session status.
 * GET /api/v1/reports/{session_id}
 */
export async function fetchReport(sessionId) {
  const response = await api.get(`/reports/${sessionId}`);
  return response.data;
}
