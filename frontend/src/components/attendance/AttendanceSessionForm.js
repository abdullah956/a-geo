import React, { useState } from 'react';
import { attendanceService } from '../../services/attendanceService';
import { locationService } from '../../services/locationService';
import './AttendanceSessionForm.css';

const AttendanceSessionForm = ({ onSessionCreated, onCancel, courses }) => {
  const [formData, setFormData] = useState({
    course: '',
    title: 'lecture',
    description: '',
    classroom_name: '',
    classroom_latitude: '',
    classroom_longitude: '',
    allowed_radius: 50,
    scheduled_duration: 60
  });
  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // If course is changed, update classroom name automatically
    if (name === 'course' && value) {
      const selectedCourse = courses.find(course => course.id.toString() === value);
      setFormData(prev => ({
        ...prev,
        [name]: value,
        classroom_name: selectedCourse ? selectedCourse.classroom : ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const getCurrentLocation = async () => {
    setLocationLoading(true);
    setErrors(prev => ({ ...prev, location: '' })); // Clear previous errors
    
    try {
      console.log('Requesting location...');
      const location = await locationService.getCurrentLocation();
      console.log('Location received:', location);
      
      setFormData(prev => ({
        ...prev,
        classroom_latitude: location.latitude.toFixed(8),
        classroom_longitude: location.longitude.toFixed(8)
      }));
      
      // Clear any location errors
      setErrors(prev => ({ ...prev, location: '' }));
    } catch (error) {
      console.error('Location error:', error);
      setErrors(prev => ({
        ...prev,
        location: error.message
      }));
    } finally {
      setLocationLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const sessionData = {
        ...formData,
        classroom_latitude: parseFloat(formData.classroom_latitude),
        classroom_longitude: parseFloat(formData.classroom_longitude),
        allowed_radius: parseInt(formData.allowed_radius),
        scheduled_duration: parseInt(formData.scheduled_duration)
      };

      const session = await attendanceService.createSession(sessionData);
      onSessionCreated(session);
    } catch (error) {
      if (error.detail) {
        setErrors({ general: error.detail });
      } else if (typeof error === 'object') {
        setErrors(error);
      } else {
        setErrors({ general: error });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="attendance-session-form">
      <div className="form-header">
        <h3>Start Attendance Session</h3>
        <p>Create a new attendance session for your course</p>
      </div>

      <form onSubmit={handleSubmit} className="session-form">
        {errors.general && (
          <div className="error-message general-error">
            {errors.general}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="course">Course *</label>
          <select
            id="course"
            name="course"
            value={formData.course}
            onChange={handleInputChange}
            required
            className={errors.course ? 'error' : ''}
          >
            <option value="">Select a course</option>
            {courses.map(course => (
              <option key={course.id} value={course.id}>
                {course.code}: {course.title}
              </option>
            ))}
          </select>
          {errors.course && (
            <span className="error-text">{errors.course}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="title">Session Title *</label>
          <select
            id="title"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            required
            className={errors.title ? 'error' : ''}
          >
            <option value="lecture">Lecture</option>
            <option value="labs">Labs</option>
            <option value="tests">Tests</option>
            <option value="other">Other</option>
          </select>
          {errors.title && (
            <span className="error-text">{errors.title}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            placeholder="Optional session description"
            rows="3"
          />
        </div>

        <div className="form-group">
          <label htmlFor="classroom_name">Classroom Name *</label>
          <input
            type="text"
            id="classroom_name"
            name="classroom_name"
            value={formData.classroom_name}
            placeholder="Select a course to see classroom"
            required
            readOnly
            className={`${errors.classroom_name ? 'error' : ''} readonly-field`}
          />
          {errors.classroom_name && (
            <span className="error-text">{errors.classroom_name}</span>
          )}
        </div>

        <div className="location-section">
          <h4>Classroom Location</h4>
          <div className="location-inputs">
            <div className="form-group">
              <label htmlFor="classroom_latitude">Latitude *</label>
              <input
                type="number"
                id="classroom_latitude"
                name="classroom_latitude"
                value={formData.classroom_latitude}
                onChange={handleInputChange}
                placeholder="e.g., 40.7128"
                step="any"
                required
                className={errors.classroom_latitude ? 'error' : ''}
              />
              {errors.classroom_latitude && (
                <span className="error-text">{errors.classroom_latitude}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="classroom_longitude">Longitude *</label>
              <input
                type="number"
                id="classroom_longitude"
                name="classroom_longitude"
                value={formData.classroom_longitude}
                onChange={handleInputChange}
                placeholder="e.g., -74.0060"
                step="any"
                required
                className={errors.classroom_longitude ? 'error' : ''}
              />
              {errors.classroom_longitude && (
                <span className="error-text">{errors.classroom_longitude}</span>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={getCurrentLocation}
            disabled={locationLoading}
            className="location-btn"
          >
            {locationLoading ? 'Getting Location...' : 'Use Current Location'}
          </button>
          {errors.location && (
            <span className="error-text">{errors.location}</span>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="allowed_radius">Allowed Radius (meters) *</label>
            <input
              type="number"
              id="allowed_radius"
              name="allowed_radius"
              value={formData.allowed_radius}
              onChange={handleInputChange}
              min="20"
              max="500"
              required
              className={errors.allowed_radius ? 'error' : ''}
            />
            {errors.allowed_radius && (
              <span className="error-text">{errors.allowed_radius}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="scheduled_duration">Duration (minutes) *</label>
            <input
              type="number"
              id="scheduled_duration"
              name="scheduled_duration"
              value={formData.scheduled_duration}
              onChange={handleInputChange}
              min="5"
              max="300"
              required
              className={errors.scheduled_duration ? 'error' : ''}
            />
            {errors.scheduled_duration && (
              <span className="error-text">{errors.scheduled_duration}</span>
            )}
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={onCancel}
            className="cancel-btn"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="submit-btn"
            disabled={loading}
          >
            {loading ? 'Creating Session...' : 'Start Session'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AttendanceSessionForm;
