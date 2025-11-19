import React, { useState, useEffect, useRef } from 'react';
import { profileService } from '../../services/profileService';
import { getBackendBaseUrl } from '../../utils/backendUrl';
import './Profile.css';

const Profile = ({ onBack }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [imageUploading, setImageUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: ''
  });
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      console.log('Fetching profile...');
      const profileData = await profileService.getProfile();
      console.log('Profile data received:', profileData);
      setProfile(profileData);
      setFormData({
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        email: profileData.email
      });
      if (profileData.profile_picture) {
        // Check if the URL already includes the domain
        const imageUrl = profileData.profile_picture.startsWith('http') 
          ? profileData.profile_picture 
          : `${getBackendBaseUrl()}${profileData.profile_picture}`;
        console.log('Setting image preview:', imageUrl);
        setImagePreview(imageUrl);
      } else {
        console.log('No profile picture found');
        setImagePreview(null);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      setMessage('Error loading profile');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleImageUpload = async () => {
    if (!selectedImage) return;

    console.log('Starting image upload...');
    console.log('Selected image:', selectedImage);
    console.log('Image type:', selectedImage.type);
    console.log('Image size:', selectedImage.size);

    try {
      setImageUploading(true);
      const result = await profileService.uploadProfileImage(selectedImage);
      console.log('Upload result:', result);
      setMessage('Profile image updated successfully!');
      setSelectedImage(null);
      // Refresh profile to get new image URL
      await fetchProfile();
    } catch (error) {
      console.error('Error uploading image:', error);
      console.error('Error details:', error.response?.data);
      setMessage(`Error uploading image: ${error.response?.data?.profile_picture?.[0] || error.message}`);
    } finally {
      setImageUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await profileService.updateProfileInfo(formData);
      setMessage('Profile updated successfully!');
      // Refresh profile data
      await fetchProfile();
    } catch (error) {
      console.error('Error updating profile:', error);
      setMessage('Error updating profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="loading">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <button className="back-btn" onClick={onBack}>
          ← Back to Dashboard
        </button>
        <h1>Profile Settings</h1>
      </div>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="profile-content">
        <div className="profile-image-section">
          <div className="image-container">
            <img
              src={imagePreview || '/default-avatar.svg'}
              alt="Profile"
              className="profile-image"
            />
          </div>

          <div className="image-controls">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageChange}
              accept="image/*"
              style={{ display: 'none' }}
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => fileInputRef.current?.click()}
            >
              Choose New Photo
            </button>

            {selectedImage && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleImageUpload}
                disabled={imageUploading}
              >
                {imageUploading ? 'Uploading...' : 'Upload Photo'}
              </button>
            )}
          </div>

          <p className="image-note">
            Profile picture is optional. Recommended size: 200x200px.
          </p>
        </div>

        <div className="profile-form-section">
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-group">
              <label htmlFor="first_name">First Name</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                disabled
              />
              <small className="form-note">Email cannot be changed</small>
            </div>

            <div className="form-group">
              <label>Role</label>
              <input
                type="text"
                value={profile?.role}
                disabled
                className="role-display"
              />
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
