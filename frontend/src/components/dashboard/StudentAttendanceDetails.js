import React, { useState, useEffect } from 'react';
import { attendanceService } from '../../services/attendanceService';
import './Dashboard.css';

const StudentAttendanceDetails = ({ onBack }) => {
  const [attendanceData, setAttendanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAttendanceDetails();
  }, []);

  const fetchAttendanceDetails = async () => {
    try {
      setLoading(true);
      const data = await attendanceService.getStudentAttendancePercentage();
      setAttendanceData(data);
    } catch (error) {
      console.error('Error fetching attendance details:', error);
      setError('Failed to load attendance details');
    } finally {
      setLoading(false);
    }
  };

  const getPercentageColor = (percentage) => {
    if (percentage >= 80) return '#10b981'; // Green
    if (percentage >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const getPercentageStatus = (percentage) => {
    if (percentage >= 80) return 'Excellent';
    if (percentage >= 60) return 'Good';
    if (percentage >= 40) return 'Fair';
    return 'Poor';
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-loading">Loading attendance details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
          <button onClick={onBack} className="back-btn">← Back to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="user-info">
          <h1>Attendance Details</h1>
          <p>Your attendance statistics and course breakdown</p>
        </div>
        <button onClick={onBack} className="back-btn">
          ← Back to Dashboard
        </button>
      </header>

      <main className="dashboard-main">
        <div className="attendance-details">
          {/* Overall Statistics */}
          <div className="attendance-overview">
            <div className="overview-card overall-card">
              <div className="overview-header">
                <h3>Overall Attendance</h3>
                <span 
                  className="overall-percentage"
                  style={{ color: getPercentageColor(attendanceData?.overall_percentage || 0) }}
                >
                  {attendanceData?.overall_percentage || 0}%
                </span>
              </div>
              <div className="overview-stats">
                <div className="overview-stat">
                  <span className="stat-number">{attendanceData?.attended_sessions || 0}</span>
                  <span className="stat-label">Sessions Attended</span>
                </div>
                <div className="overview-stat">
                  <span className="stat-number">{attendanceData?.total_sessions || 0}</span>
                  <span className="stat-label">Total Sessions</span>
                </div>
                <div className="overview-stat">
                  <span className="stat-number missed">{attendanceData?.missed_sessions || 0}</span>
                  <span className="stat-label">Missed Sessions</span>
                </div>
                <div className="overview-stat">
                  <span className="stat-number">{attendanceData?.courses_count || 0}</span>
                  <span className="stat-label">Enrolled Courses</span>
                </div>
              </div>
              <div className="status-indicator">
                <span 
                  className="status-badge"
                  style={{ 
                    backgroundColor: getPercentageColor(attendanceData?.overall_percentage || 0),
                    color: 'white'
                  }}
                >
                  {getPercentageStatus(attendanceData?.overall_percentage || 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Course-wise Breakdown */}
          <div className="courses-breakdown">
            <h3>Course-wise Attendance</h3>
            {attendanceData?.course_statistics && attendanceData.course_statistics.length > 0 ? (
              <div className="courses-grid">
                {attendanceData.course_statistics.map((course) => (
                  <div key={course.course_id} className="course-attendance-card">
                    <div className="course-header">
                      <div className="course-title">
                        <h4>{course.course_code}</h4>
                        <p>{course.course_title}</p>
                      </div>
                      <div 
                        className="course-percentage-badge"
                        style={{ backgroundColor: getPercentageColor(course.attendance_percentage) }}
                      >
                        {course.attendance_percentage}%
                      </div>
                    </div>
                    
                    <div className="course-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ 
                            width: `${course.attendance_percentage}%`,
                            backgroundColor: getPercentageColor(course.attendance_percentage)
                          }}
                        ></div>
                      </div>
                    </div>

                    <div className="course-stats">
                      <div className="course-stat">
                        <span className="stat-value">{course.attended_sessions}</span>
                        <span className="stat-label">Attended</span>
                      </div>
                      <div className="course-stat">
                        <span className="stat-value">{course.total_sessions}</span>
                        <span className="stat-label">Total</span>
                      </div>
                      <div className="course-stat">
                        <span className="stat-value missed">
                          {course.total_sessions - course.attended_sessions}
                        </span>
                        <span className="stat-label">Missed</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-courses-message">
                <h4>No Course Data Available</h4>
                <p>You don't have any attendance records yet.</p>
              </div>
            )}
          </div>

          {/* Attendance Tips */}
          <div className="attendance-tips">
            <h3>Attendance Tips</h3>
            <div className="tips-grid">
              <div className="tip-card">
                <div className="tip-icon">📅</div>
                <h4>Stay Consistent</h4>
                <p>Regular attendance helps you stay on track with course material and improves your learning outcomes.</p>
              </div>
              <div className="tip-card">
                <div className="tip-icon">⏰</div>
                <h4>Be Punctual</h4>
                <p>Arrive on time to avoid missing important announcements and to show respect for your instructors.</p>
              </div>
              <div className="tip-card">
                <div className="tip-icon">📱</div>
                <h4>Use the App</h4>
                <p>Make sure to mark your attendance through the app when sessions are active to avoid being marked absent.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default StudentAttendanceDetails;
