import React, { useState, useEffect } from 'react';
import { attendanceService } from '../../services/attendanceService';
import AttendanceSessionForm from './AttendanceSessionForm';
import './AttendanceSessionManager.css';

const AttendanceSessionManager = ({ courses, onBack }) => {
  const [sessions, setSessions] = useState([]);
  const [activeSessions, setActiveSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchSessions();
    fetchStats();
  }, []);

  const fetchSessions = async () => {
    try {
      const sessionsData = await attendanceService.getSessions();
      console.log('Sessions data received:', sessionsData);
      // Handle paginated response
      const sessions = sessionsData?.results || sessionsData || [];
      console.log('Processed sessions:', sessions);
      setSessions(Array.isArray(sessions) ? sessions : []);
      
      const activeData = await attendanceService.getActiveSessions();
      console.log('Active sessions data received:', activeData);
      console.log('First active session:', activeData?.[0]);
      setActiveSessions(Array.isArray(activeData) ? activeData : []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setSessions([]);
      setActiveSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const statsData = await attendanceService.getStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleCreateSession = async (sessionData) => {
    try {
      setSessions(prev => [sessionData, ...(prev || [])]);
      setActiveSessions(prev => [sessionData, ...(prev || [])]);
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const handleEndSession = async (sessionId) => {
    try {
      await attendanceService.endSession(sessionId);
      setSessions(prev => 
        (prev || []).map(session => 
          session.id === sessionId 
            ? { ...session, status: 'ended', ended_at: new Date().toISOString() }
            : session
        )
      );
      setActiveSessions(prev => 
        (prev || []).filter(session => session.id !== sessionId)
      );
      setSelectedSession(null);
    } catch (error) {
      console.error('Error ending session:', error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      active: 'status-active',
      ended: 'status-ended',
      cancelled: 'status-cancelled'
    };
    return statusClasses[status] || 'status-unknown';
  };

  if (loading) {
    return (
      <div className="attendance-manager-loading">
        <div className="loading-spinner"></div>
        <p>Loading attendance sessions...</p>
      </div>
    );
  }

  if (showCreateForm) {
    return (
      <AttendanceSessionForm
        courses={courses}
        onSessionCreated={handleCreateSession}
        onCancel={() => setShowCreateForm(false)}
      />
    );
  }

  return (
    <div className="attendance-session-manager">
      <div className="manager-header">
        <button onClick={onBack} className="back-btn">
          ← Back to Dashboard
        </button>
        <div className="header-content">
          <h2>Attendance Management</h2>
          <p>Manage attendance sessions for your courses</p>
        </div>
        <button 
          onClick={() => setShowCreateForm(true)}
          className="create-session-btn"
        >
          Start New Session
        </button>
      </div>

      {stats && (
        <div className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <h3>{stats.total_sessions}</h3>
              <p>Total Sessions</p>
            </div>
            <div className="stat-card">
              <h3>{stats.active_sessions}</h3>
              <p>Active Sessions</p>
            </div>
            <div className="stat-card">
              <h3>{stats.total_attendance_marked}</h3>
              <p>Attendance Marked</p>
            </div>
            <div className="stat-card">
              <h3>{stats.attendance_rate}%</h3>
              <p>Attendance Rate</p>
            </div>
          </div>
        </div>
      )}

      <div className="sessions-section">
        <div className="section-header">
          <h3>Active Sessions ({activeSessions.length})</h3>
        </div>
        
        {activeSessions.length > 0 ? (
          <div className="sessions-grid">
            {activeSessions.map(session => {
              console.log('Rendering active session:', session);
              return (
              <div key={session.id} className="session-card active">
                <div className="session-header">
                  <h4>{session.title}</h4>
                  <span className={`status-badge ${getStatusBadge(session.status)}`}>
                    {session.status?.toUpperCase() || 'UNKNOWN'}
                  </span>
                </div>
                
                <div className="session-info">
                  <p><strong>Course:</strong> {session.course_code || 'N/A'}</p>
                  <p><strong>Classroom:</strong> {session.classroom_name || 'N/A'}</p>
                  <p><strong>Started:</strong> {formatDate(session.started_at)}</p>
                  <p><strong>Duration:</strong> {session.duration_minutes ? session.duration_minutes.toFixed(1) : 'N/A'} minutes</p>
                </div>

                <div className="session-stats">
                  <div className="stat">
                    <span className="stat-label">Attendance:</span>
                    <span className="stat-value">
                      {session.attendance_count || 0}/{session.total_enrolled || 0}
                    </span>
                  </div>
                </div>

                <div className="session-actions">
                  <button
                    onClick={() => setSelectedSession(session)}
                    className="action-btn view-btn"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleEndSession(session.id)}
                    className="action-btn end-btn"
                  >
                    End Session
                  </button>
                </div>
              </div>
              );
            })}
          </div>
        ) : (
          <div className="no-sessions">
            <h4>No Active Sessions</h4>
            <p>Start a new attendance session to begin tracking attendance.</p>
          </div>
        )}
      </div>

      <div className="sessions-section">
        <div className="section-header">
          <h3>Recent Sessions ({sessions.length})</h3>
        </div>
        
        {sessions.length > 0 ? (
          <div className="sessions-list">
            {sessions.slice(0, 5).map(session => (
              <div key={session.id} className="session-item">
                <div className="session-info">
                  <h4>{session.title || 'Untitled Session'}</h4>
                  <p>{session.course_code || 'N/A'} • {session.classroom_name || 'N/A'}</p>
                  <p>Started: {formatDate(session.started_at)}</p>
                </div>
                <div className="session-meta">
                  <span className={`status-badge ${getStatusBadge(session.status)}`}>
                    {session.status?.toUpperCase() || 'UNKNOWN'}
                  </span>
                  <span className="attendance-count">
                    {session.attendance_count || 0}/{session.total_enrolled || 0}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-sessions">
            <h4>No Sessions Yet</h4>
            <p>Create your first attendance session to get started.</p>
          </div>
        )}
      </div>

      {selectedSession && (
        <div className="session-details-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>{selectedSession.title}</h3>
              <button
                onClick={() => setSelectedSession(null)}
                className="close-btn"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="session-details">
                <div className="detail-section">
                  <h4>Session Information</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <span className="detail-label">Course:</span>
                      <span className="detail-value">{selectedSession.course_code}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Classroom:</span>
                      <span className="detail-value">{selectedSession.classroom_name}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Started:</span>
                      <span className="detail-value">{formatDate(selectedSession.started_at)}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Status:</span>
                      <span className={`detail-value ${getStatusBadge(selectedSession.status)}`}>
                        {selectedSession.status?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="detail-section">
                  <h4>Attendance Summary</h4>
                  <div className="attendance-summary">
                    <div className="summary-stat">
                      <span className="summary-label">Total Enrolled:</span>
                      <span className="summary-value">{selectedSession.total_enrolled}</span>
                    </div>
                    <div className="summary-stat">
                      <span className="summary-label">Attendance Marked:</span>
                      <span className="summary-value">{selectedSession.attendance_count}</span>
                    </div>
                    <div className="summary-stat">
                      <span className="summary-label">Attendance Rate:</span>
                      <span className="summary-value">
                        {selectedSession.total_enrolled > 0 
                          ? ((selectedSession.attendance_count / selectedSession.total_enrolled) * 100).toFixed(1)
                          : 0}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button
                onClick={() => setSelectedSession(null)}
                className="close-modal-btn"
              >
                Close
              </button>
              {selectedSession.status === 'active' && (
                <button
                  onClick={() => handleEndSession(selectedSession.id)}
                  className="end-session-btn"
                >
                  End Session
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendanceSessionManager;
