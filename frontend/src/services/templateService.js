/**
 * Netran AI — Template Mock Interview Service.
 * Communicates with the /api/v1/template endpoints.
 */

import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Build axios headers with the bearer token from the auth store.
 */
function authHeaders() {
  const token = useAuthStore.getState().token;
  return { Authorization: `Bearer ${token}` };
}

/**
 * Fetch the list of all available pre-built mock interview templates.
 * @returns {Promise<{ templates: Array, total: number }>}
 */
export async function fetchTemplates() {
  const response = await axios.get(`${API_BASE}/template/list`, {
    headers: authHeaders(),
  });
  return response.data;
}

/**
 * Create a new pre-hydrated interview session from a template pack.
 * The session is immediately in READY status and can be used for voice interview.
 *
 * @param {'backend' | 'frontend' | 'fullstack'} templateId
 * @returns {Promise<{ session_id: string, template_id: string, target_role: string, status: string, message: string }>}
 */
export async function startTemplateSession(templateId) {
  const response = await axios.post(
    `${API_BASE}/template/start`,
    { template_id: templateId },
    { headers: authHeaders() }
  );
  return response.data;
}
