import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import './Dashboard.css';

const StudentDashboard = () => {
  const [user, setUser] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showEnrollments, setShowEnrollments] = useState(false);
  const [selectedEnrollment, setSelectedEnrollment] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const userData = authService.getCurrentUser();
        setUser(userData);
        
        const dashboard = await authService.getDashboard();
        setDashboardData(dashboard);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleLogout = async () => {
    try {
      await authService.logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="user-info">
          <h1>Welcome, {user?.first_name}!</h1>
          <p>Student Dashboard</p>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </header>

      <main className="dashboard-main">
        {!showEnrollments ? (
          <>
            <div className="dashboard-welcome">
              <h2>{dashboardData?.message}</h2>
              <p>You are logged in as a Student</p>
            </div>

            <div className="dashboard-grid">
              <div className="dashboard-card courses-card">
                <h3>My Courses ({dashboardData?.enrollments_count || 0})</h3>
                <p>View and manage your enrolled courses</p>
                <button
                  className="card-btn"
                  onClick={() => setShowEnrollments(true)}
                >
                  View Courses
                </button>
              </div>

          <div className="dashboard-card">
            <h3>Assignments</h3>
            <p>Submit and track your assignments</p>
            <button className="card-btn">View Assignments</button>
          </div>

          <div className="dashboard-card">
            <h3>Progress</h3>
            <p>Track your learning progress</p>
            <button className="card-btn">View Progress</button>
          </div>

              <div className="dashboard-card">
                <h3>Assignments</h3>
                <p>Submit and track your assignments</p>
                <button className="card-btn">View Assignments</button>
              </div>

              <div className="dashboard-card">
                <h3>Progress</h3>
                <p>Track your learning progress</p>
                <button className="card-btn">View Progress</button>
              </div>

              <div className="dashboard-card">
                <h3>Profile</h3>
                <p>Manage your account settings</p>
                <button className="card-btn">Edit Profile</button>
              </div>
            </div>

            <div className="features-section">
              <h3>Available Features</h3>
              <ul className="features-list">
                {dashboardData?.features?.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </div>
          </>
        ) : (
          <div className="enrollments-management">
            <div className="enrollments-header">
              <button
                className="back-btn"
                onClick={() => setShowEnrollments(false)}
              >
                ← Back to Dashboard
              </button>
              <h2>My Enrolled Courses</h2>
              <p>View and manage your course enrollments</p>
            </div>

            <div className="enrollments-grid">
              {dashboardData?.enrollments && dashboardData.enrollments.length > 0 ? (
                dashboardData.enrollments.map((enrollment) => (
                  <div key={enrollment.id} className="enrollment-card">
                    <div className="enrollment-header">
                      <h3>{enrollment.course_code}: {enrollment.course_title}</h3>
                      <span className="enrollment-status active">Enrolled</span>
                    </div>

                    <div className="enrollment-body">
                      <div className="enrollment-info">
                        <div className="info-item">
                          <span className="info-label">Enrollment Date:</span>
                          <span className="info-value">
                            {new Date(enrollment.enrolled_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Current Grade:</span>
                          <span className={`info-value ${enrollment.grade ? 'graded' : 'ungraded'}`}>
                            {enrollment.grade ? `${enrollment.grade}%` : 'Not graded yet'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="enrollment-actions">
                      <button
                        className="action-btn view-btn"
                        onClick={() => setSelectedEnrollment(enrollment)}
                      >
                        View Details
                      </button>
                      <button className="action-btn unenroll-btn">Unenroll</button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-enrollments-card">
                  <h3>No Course Enrollments</h3>
                  <p>You are not enrolled in any courses yet. Contact your teacher or administrator to enroll in courses.</p>
                </div>
              )}
            </div>

            {selectedEnrollment && (
              <div className="enrollment-details-modal">
                <div className="enrollment-details-content">
                  <div className="enrollment-details-header">
                    <h3>{selectedEnrollment.course_code}: {selectedEnrollment.course_title}</h3>
                    <button
                      className="close-btn"
                      onClick={() => setSelectedEnrollment(null)}
                    >
                      ×
                    </button>
                  </div>
                  <div className="enrollment-details-body">
                    <div className="enrollment-details-section">
                      <h4>Enrollment Information</h4>
                      <div className="enrollment-info-grid">
                        <div className="info-item">
                          <span className="info-label">Course Code:</span>
                          <span className="info-value">{selectedEnrollment.course_code}</span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Enrollment Date:</span>
                          <span className="info-value">
                            {new Date(selectedEnrollment.enrolled_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Current Grade:</span>
                          <span className={`info-value ${selectedEnrollment.grade ? 'graded' : 'ungraded'}`}>
                            {selectedEnrollment.grade ? `${selectedEnrollment.grade}%` : 'Not graded yet'}
                          </span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Status:</span>
                          <span className="info-value active">Active Enrollment</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default StudentDashboard;
