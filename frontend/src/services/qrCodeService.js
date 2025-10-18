import api from './api';

export const qrCodeService = {
  // Generate QR code token for a session
  generateToken: async (sessionId, durationMinutes = 10) => {
    try {
      const response = await api.post(`/attendance/sessions/${sessionId}/generate-token/`, {
        duration_minutes: durationMinutes
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Refresh QR code token
  refreshToken: async (sessionId, oldToken = null) => {
    try {
      const response = await api.post(`/attendance/sessions/${sessionId}/refresh-token/`, {
        old_token: oldToken
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Verify QR code token and mark attendance
  verifyToken: async (token, latitude = null, longitude = null) => {
    try {
      const data = { token };
      if (latitude !== null && longitude !== null) {
        data.latitude = latitude;
        data.longitude = longitude;
      }
      
      const response = await api.post('/attendance/verify-token/', data);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};

