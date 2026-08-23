import api from './api';

export const notificationsService = {
  /**
   * Fetch all notifications and unread count for current candidate user.
   * @returns {Promise<{ notifications: Array, unread_count: number }>}
   */
  async getNotifications() {
    const response = await api.get('/notifications');
    return response.data;
  },

  /**
   * Mark a specific notification as read.
   * @param {string} id - Notification UUID
   * @returns {Promise<Object>} Updated notification object
   */
  async markAsRead(id) {
    const response = await api.patch(`/notifications/${id}/read`);
    return response.data;
  },

  /**
   * Mark all unread notifications as read.
   * @returns {Promise<{ message: string, unread_count: number }>}
   */
  async markAllAsRead() {
    const response = await api.post('/notifications/mark-all-read');
    return response.data;
  },

  /**
   * Delete a notification from candidate history.
   * @param {string} id - Notification UUID
   * @returns {Promise<{ message: string }>}
   */
  async deleteNotification(id) {
    const response = await api.delete(`/notifications/${id}`);
    return response.data;
  },
};

export default notificationsService;
