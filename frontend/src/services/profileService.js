import api from './api';

const PROFILE_URL = '/auth/profile/';

export const profileService = {
  // Get user profile
  getProfile: async () => {
    const response = await api.get(PROFILE_URL);
    return response.data;
  },

  // Update user profile
  updateProfile: async (profileData) => {
    const response = await api.patch(PROFILE_URL, profileData);
    // Update localStorage with new user data
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  },

  // Upload profile image
  uploadProfileImage: async (imageFile) => {
    console.log('Uploading profile image:', imageFile);
    const formData = new FormData();
    formData.append('profile_picture', imageFile);

    console.log('FormData contents:');
    for (let [key, value] of formData.entries()) {
      console.log(key, value);
    }

    try {
      const response = await api.patch(PROFILE_URL, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('Upload response:', response.data);

      // Update localStorage with new user data including the profile image
      if (response.data) {
        localStorage.setItem('user', JSON.stringify(response.data));
        console.log('Updated localStorage with:', response.data);
      }
      return response.data;
    } catch (error) {
      console.error('Upload error:', error);
      console.error('Error response:', error.response?.data);
      throw error;
    }
  },

  // Update profile without image
  updateProfileInfo: async (profileData) => {
    const response = await api.patch(PROFILE_URL, profileData);
    // Update localStorage with new user data
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  }
};
