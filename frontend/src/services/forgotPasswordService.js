import api from './api';

const forgotPasswordService = {
  // Step 1: Request password reset - send OTP to email
  requestPasswordReset: async (email) => {
    try {
      const response = await api.post('/auth/forgot-password/request/', { email });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Step 2: Verify OTP code
  verifyOTP: async (email, otp) => {
    try {
      const response = await api.post('/auth/forgot-password/verify-otp/', { 
        email, 
        otp 
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Step 3: Reset password with new password
  resetPassword: async (email, otp, newPassword) => {
    try {
      const response = await api.post('/auth/forgot-password/reset/', { 
        email, 
        otp, 
        new_password: newPassword 
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};

export default forgotPasswordService;
