import React, { useState, useEffect } from 'react';
import { attendanceService } from '../../services/attendanceService';
import { autoAttendanceService } from '../../services/autoAttendanceService';
import { locationService } from '../../services/locationService';
import './AttendanceNotificationBanner.css';

const AttendanceNotificationBanner = () => {
  const [activeSessions, setActiveSessions] = useState([]);
  const [showBanner, setShowBanner] = useState(false);
  const [loading, setLoading] = useState(true);
  const [locationPermission, setLocationPermission] = useState(null);

  useEffect(() => {
    // Only start checking if user is authenticated
    const isAuthenticated = !!localStorage.getItem('access');
    if (isAuthenticated) {
      checkActiveSessions();
      checkLocationPermission();
      
      // Check for active sessions every 30 seconds
      const interval = setInterval(checkActiveSessions, 30000);
      
      // Listen for attendance marked events
      const handleAttendanceMarked = () => {
        checkActiveSessions();
      };
      
      window.addEventListener('attendance-marked', handleAttendanceMarked);
      
      return () => {
        clearInterval(interval);
        window.removeEventListener('attendance-marked', handleAttendanceMarked);
      };
    }
  }, []);

  const checkActiveSessions = async () => {
    try {
      // Check if user is still authenticated before making API call
      const isAuthenticated = !!localStorage.getItem('access');
      if (!isAuthenticated) {
        console.log('User not authenticated, skipping notifications check');
        return;
      }

      const notifications = await attendanceService.getStudentNotifications();
      console.log('Banner notifications data:', notifications);
      
      // Filter out sessions that are already marked
      const unmarkedSessions = notifications.active_sessions.filter(session => !session.attendance_marked);
      console.log('Banner unmarked sessions:', unmarkedSessions);
      
      setActiveSessions(unmarkedSessions);
      setShowBanner(unmarkedSessions.length > 0);
    } catch (error) {
      console.error('Error checking active sessions:', error);
      // Don't show banner if there's an authentication error
      if (error.response?.status === 401) {
        console.log('Authentication error, hiding notifications');
        setShowBanner(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const checkLocationPermission = async () => {
    try {
      // Check if we already have permission without requesting it
      if (navigator.permissions) {
        const permission = await navigator.permissions.query({ name: 'geolocation' });
        setLocationPermission(permission.state === 'granted');
      } else {
        // Fallback: assume no permission initially
        setLocationPermission(false);
      }
    } catch (error) {
      console.error('Error checking location permission:', error);
      setLocationPermission(false);
    }
  };

  const requestLocationPermission = async () => {
    try {
      // Directly try to get location - this will trigger browser permission dialog
      await locationService.getCurrentLocation();
      setLocationPermission(true);
      // Refresh the banner to show Mark Attendance button
      await checkActiveSessions();
    } catch (error) {
      console.error('Error requesting location permission:', error);
      setLocationPermission(false);
    }
  };

  const handleMarkAttendance = async (session) => {
    try {
      await autoAttendanceService.startAutomaticAttendance(session);
      // Refresh the banner after successful attendance marking
      await checkActiveSessions();
    } catch (error) {
      console.error('Error marking attendance:', error);
    }
  };

  const handleDismiss = () => {
    setShowBanner(false);
  };

  if (loading || !showBanner || activeSessions.length === 0) {
    return null;
  }

  return (
    <div className="attendance-notification-banner">
      <div className="banner-content">
        <div className="banner-icon">📚</div>
        <div className="banner-text">
          <h4>Active Attendance Sessions</h4>
          <p>
            {activeSessions.length === 1 
              ? `You have 1 active attendance session`
              : `You have ${activeSessions.length} active attendance sessions`
            }
          </p>
        </div>
        <div className="banner-actions">
          {activeSessions.map(session => (
            !locationPermission ? (
              <button
                key={session.id}
                onClick={requestLocationPermission}
                className="enable-location-btn"
              >
                Enable Location Access
              </button>
            ) : (
              <button
                key={session.id}
                onClick={() => handleMarkAttendance(session)}
                className="mark-attendance-btn"
              >
                Mark Attendance
              </button>
            )
          ))}
          <button
            onClick={handleDismiss}
            className="dismiss-btn"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  );
};

export default AttendanceNotificationBanner;
