import React, { useState, useEffect } from 'react';
import { attendanceService } from '../../services/attendanceService';
import { locationService } from '../../services/locationService';
import './StudentAttendancePanel.css';

const StudentAttendancePanel = ({ onBack }) => {
  const [activeSessions, setActiveSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [locationPermission, setLocationPermission] = useState(null);
  const [markingAttendance, setMarkingAttendance] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchActiveSessions();
    checkLocationPermission();
  }, []);

  const fetchActiveSessions = async () => {
    try {
      const notifications = await attendanceService.getStudentNotifications();
      console.log('Notifications data:', notifications);
      
      // Filter out sessions that are already marked
      const unmarkedSessions = notifications.active_sessions.filter(session => !session.attendance_marked);
      console.log('Unmarked sessions:', unmarkedSessions);
      
      setActiveSessions(unmarkedSessions);
    } catch (error) {
      console.error('Error fetching active sessions:', error);
      setError('Failed to load attendance sessions');
    } finally {
      setLoading(false);
    }
  };

  const checkLocationPermission = async () => {
    try {
      const hasPermission = await locationService.requestLocationPermission();
      setLocationPermission(hasPermission);
    } catch (error) {
      console.error('Error checking location permission:', error);
      setLocationPermission(false);
    }
  };

  const handleMarkAttendance = async (session) => {
    if (!locationPermission) {
      setError('Location permission is required to mark attendance');
      return;
    }

    setMarkingAttendance(session.id);
    setError(null);

    try {
      // Get current location
      const location = await locationService.getCurrentLocation();
      console.log('Location obtained:', location);
      console.log('Session ID:', session.id);
      console.log('Session details:', session);
      
      // Mark attendance
      const result = await attendanceService.markAttendance(
        session.id,
        location.latitude,
        location.longitude
      );

      console.log('Attendance marking result:', result);
      
      if (result.location_verified) {
        // Refresh the sessions list to remove the marked session
        await fetchActiveSessions();
        setError(null); // Clear any previous errors
        
        // Dispatch event to refresh banner
        window.dispatchEvent(new CustomEvent('attendance-marked', {
          detail: { sessionId: session.id }
        }));
      } else {
        setError(`Location verification failed. You must be within ${session.allowed_radius}m of the classroom.`);
      }
    } catch (error) {
      console.error('Error marking attendance:', error);
      if (error.detail) {
        setError(error.detail);
      } else if (error.message) {
        setError(error.message);
      } else {
        setError('Failed to mark attendance');
      }
    } finally {
      setMarkingAttendance(null);
    }
  };

  const requestLocationPermission = async () => {
    try {
      // Directly try to get location - this will trigger browser permission dialog
      await locationService.getCurrentLocation();
      setLocationPermission(true);
      setError(null); // Clear any previous errors
    } catch (error) {
      console.error('Error requesting location permission:', error);
      setLocationPermission(false);
      if (error.message === 'Location access denied by user') {
        setError('Location permission was denied. Please allow location access to mark attendance.');
      } else {
        setError('Failed to get location permission. Please try again.');
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="attendance-panel-loading">
        <div className="loading-spinner"></div>
        <p>Loading attendance sessions...</p>
      </div>
    );
  }

  return (
    <div className="student-attendance-panel">
      <div className="panel-header">
        <button onClick={onBack} className="back-btn">
          ← Back to Dashboard
        </button>
        <div className="header-content">
          <h2>Attendance</h2>
          <p>Mark your attendance for active sessions</p>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
          <button onClick={() => setError(null)} className="close-error">
            ×
          </button>
        </div>
      )}

      {!locationPermission && (
        <div className="location-permission-banner">
          <div className="permission-content">
            <div className="permission-icon">📍</div>
            <div className="permission-text">
              <h3>Location Permission Required</h3>
              <p>To mark attendance, we need access to your location to verify you're in the classroom.</p>
            </div>
            <button 
              onClick={requestLocationPermission}
              className="permission-btn"
            >
              Enable Location
            </button>
          </div>
        </div>
      )}

      <div className="sessions-section">
        <div className="section-header">
          <h3>Active Sessions ({activeSessions.length})</h3>
        </div>

        {activeSessions.length > 0 ? (
          <div className="sessions-list">
            {activeSessions.map(session => (
              <div key={session.id} className="session-card">
                <div className="session-header">
                  <h4>{session.title}</h4>
                  <span className="session-status active">ACTIVE</span>
                </div>

                <div className="session-info">
                  <div className="info-row">
                    <span className="info-label">Course:</span>
                    <span className="info-value">{session.course_code}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Classroom:</span>
                    <span className="info-value">{session.classroom_name}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Started:</span>
                    <span className="info-value">{formatDate(session.started_at)}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Duration:</span>
                    <span className="info-value">{session.duration_minutes?.toFixed(1)} minutes</span>
                  </div>
                </div>

                <div className="session-actions">
                  {session.attendance_marked ? (
                    <div className="attendance-marked">
                      <span className="check-icon">✓</span>
                      <span>Attendance Marked</span>
                    </div>
                  ) : !locationPermission ? (
                    <button
                      onClick={requestLocationPermission}
                      className="enable-location-btn"
                    >
                      Enable Location Access
                    </button>
                  ) : (
                    <button
                      onClick={() => handleMarkAttendance(session)}
                      disabled={markingAttendance === session.id}
                      className="mark-attendance-btn"
                    >
                      {markingAttendance === session.id ? 'Marking...' : 'Mark Attendance'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-sessions">
            <div className="no-sessions-icon">📚</div>
            <h4>No Active Sessions</h4>
            <p>There are currently no active attendance sessions for your enrolled courses.</p>
          </div>
        )}
      </div>

      {locationPermission && (
        <div className="location-info">
          <div className="location-info-content">
            <span className="location-icon">📍</span>
            <span>Location access enabled</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentAttendancePanel;
