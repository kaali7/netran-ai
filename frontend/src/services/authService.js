import api from './api';

export const authService = {
  /**
   * Register a new candidate user account.
   * @param {Object} data - { email, password, role }
   * @returns {Promise<Object>} Created user object
   */
  async signup({ email, password, role = 'candidate' }) {
    const response = await api.post('/auth/signup', {
      email,
      password,
      role,
    });
    return response.data;
  },

  /**
   * Authenticate user credentials and retrieve access token.
   * @param {Object} credentials - { email, password }
   * @returns {Promise<Object>} TokenResponse { access_token, token_type, user }
   */
  async login({ email, password }) {
    const response = await api.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  /**
   * Fetch current authenticated candidate user profile.
   * @returns {Promise<Object>} User object
   */
  async getMe() {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

export default authService;
