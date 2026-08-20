import api from './api';

/**
 * Upload candidate resume file (.pdf, .docx, .txt, .tex).
 * POST /api/v1/ingest/resume (multipart/form-data)
 */
export async function uploadResume(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/ingest/resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 90000,
  });
  return response.data;
}

/**
 * Ingest raw job description text.
 * POST /api/v1/ingest/jd
 */
export async function ingestJD(rawJdText, sessionId = null) {
  const payload = {
    raw_jd_text: rawJdText,
  };
  if (sessionId) {
    payload.session_id = sessionId;
  }

  const response = await api.post('/ingest/jd', payload, {
    timeout: 90000,
  });
  return response.data;
}

/**
 * Trigger Stage 1 (Research) & Stage 2 (Question Tree) background pipeline.
 * POST /api/v1/setup/analyze
 */
export async function startAnalysis(sessionId, targetSeniority = 'Senior', forceRefresh = false) {
  const response = await api.post('/setup/analyze', {
    session_id: sessionId,
    target_seniority: targetSeniority,
    force_refresh: forceRefresh,
  });
  return response.data;
}

/**
 * Poll current background analysis progress status.
 * GET /api/v1/questions/status/{session_id}
 */
export async function pollAnalysisStatus(sessionId) {
  const response = await api.get(`/questions/status/${sessionId}`);
  return response.data;
}

/**
 * Duplicate an existing session for retaking.
 * POST /api/v1/setup/sessions/{session_id}/duplicate
 */
export async function duplicateSession(sessionId) {
  const response = await api.post(`/setup/sessions/${sessionId}/duplicate`);
  return response.data;
}

/**
 * Fetch generated 15-question tree, candidate resume analysis, and persona behavior.
 * GET /api/v1/questions/preview/{session_id}
 */
export async function getQuestionPreview(sessionId) {
  const response = await api.get(`/questions/preview/${sessionId}`);
  return response.data;
}
