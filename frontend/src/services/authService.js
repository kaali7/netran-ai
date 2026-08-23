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

  /**
   * Update current authenticated candidate user profile (e.g. display_name).
   * @param {Object} profileData - { display_name }
   * @returns {Promise<Object>} Updated User object
   */
  async updateProfile({ display_name }) {
    const response = await api.patch('/auth/profile', {
      display_name,
    });
    return response.data;
  },

  /**
   * Change user password with current password verification.
   * @param {Object} data - { current_password, new_password }
   * @returns {Promise<Object>} Message response
   */
  async changePassword({ current_password, new_password }) {
    const response = await api.post('/auth/change-password', {
      current_password,
      new_password,
    });
    return response.data;
  },
};

export default authService;
