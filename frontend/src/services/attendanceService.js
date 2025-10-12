import api from './api';

export const attendanceService = {
  // Get all attendance sessions for current user
  getSessions: async () => {
    try {
      const response = await api.get('/attendance/sessions/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get active attendance sessions
  getActiveSessions: async () => {
    try {
      const response = await api.get('/attendance/sessions/active/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get session details
  getSessionDetails: async (sessionId) => {
    try {
      const response = await api.get(`/attendance/sessions/${sessionId}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Create new attendance session (teachers only)
  createSession: async (sessionData) => {
    try {
      const response = await api.post('/attendance/sessions/create/', sessionData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // End attendance session (teachers only)
  endSession: async (sessionId) => {
    try {
      const response = await api.post(`/attendance/sessions/${sessionId}/end/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Mark attendance (students only)
  markAttendance: async (sessionId, latitude, longitude) => {
    try {
      console.log('Sending attendance data:', {
        session_id: sessionId,
        latitude: latitude,
        longitude: longitude
      });
      
      const response = await api.post('/attendance/mark/', {
        session_id: sessionId,
        latitude: latitude,
        longitude: longitude
      });
      
      console.log('API response:', response);
      return response.data;
    } catch (error) {
      console.error('Attendance service error:', error);
      throw error.response?.data || error.message;
    }
  },

  // Get student notifications and active sessions
  getStudentNotifications: async () => {
    try {
      const response = await api.get('/attendance/notifications/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Get attendance statistics (teachers and admins)
  getStats: async () => {
    try {
      const response = await api.get('/attendance/stats/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};
