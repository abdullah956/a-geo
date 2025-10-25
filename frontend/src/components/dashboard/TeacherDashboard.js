import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import Profile from '../common/Profile';
import AttendanceSessionManager from '../attendance/AttendanceSessionManager';
import TeacherStudentsView from './TeacherStudentsView';
import './Dashboard.css';

const TeacherDashboard = () => {
  const [user, setUser] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCourses, setShowCourses] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [showAttendance, setShowAttendance] = useState(false);
  const [showStudents, setShowStudents] = useState(false);

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

  const handleEditProfile = () => {
    setShowProfile(true);
  };

  const handleBackToDashboard = () => {
    setShowProfile(false);
    setShowCourses(false);
    setShowAttendance(false);
    setShowStudents(false);
    setSelectedCourse(null);
    // Refresh user data from localStorage to get updated profile picture
    const updatedUser = authService.getCurrentUser();
    console.log('Updated user data from localStorage:', updatedUser);
    if (updatedUser) {
      setUser(updatedUser);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading...</div>;
  }

  if (showProfile) {
    return <Profile onBack={handleBackToDashboard} />;
  }

  if (showAttendance) {
    return <AttendanceSessionManager courses={dashboardData?.courses || []} onBack={handleBackToDashboard} />;
  }

  if (showStudents) {
    return <TeacherStudentsView onBack={handleBackToDashboard} />;
  }

  return (
    <div className="dashboard teacher-theme">
      <header className="dashboard-header">
        <div className="user-info">
          <img
            src={user?.profile_picture ? (user.profile_picture.startsWith('http') ? user.profile_picture : `http://localhost:8000${user.profile_picture}`) : '/default-avatar.svg'}
            alt="Profile"
            className="profile-avatar"
          />
          <div>
            <h1>Welcome, {user?.first_name}!</h1>
            <p>Teacher Dashboard</p>
          </div>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </header>

      <main className="dashboard-main">
        {!showCourses ? (
          <>
            <div className="dashboard-welcome">
              <h2>{dashboardData?.message}</h2>
              <p>You are logged in as a Teacher</p>
            </div>

            <div className="dashboard-grid">
              <div className="dashboard-card courses-card">
                <h3>Manage Courses ({dashboardData?.courses_count || 0})</h3>
                <p>Create and manage your courses</p>
                <button
                  className="card-btn"
                  onClick={() => setShowCourses(true)}
                >
                  Manage Courses
                </button>
              </div>

          <div className="dashboard-card">
            <h3>View Students</h3>
            <p>Monitor student progress and performance</p>
            <button 
              className="card-btn"
              onClick={() => setShowStudents(true)}
            >
              View Students
            </button>
          </div>

              <div className="dashboard-card">
                <h3>Attendance Management</h3>
                <p>Start and manage attendance sessions</p>
                <button 
                  className="card-btn"
                  onClick={() => setShowAttendance(true)}
                >
                  Manage Attendance
                </button>
              </div>


              <div className="dashboard-card">
                <h3>Profile</h3>
                <p>Manage your account settings</p>
                <button className="card-btn" onClick={handleEditProfile}>Edit Profile</button>
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
          <div className="courses-management">
            <div className="courses-header">
              <button
                className="back-btn"
                onClick={() => setShowCourses(false)}
              >
                ← Back to Dashboard
              </button>
              <h2>Your Assigned Courses</h2>
              <p>Manage and view details of your courses</p>
            </div>

            <div className="courses-grid">
              {dashboardData?.courses && dashboardData.courses.length > 0 ? (
                dashboardData.courses.map((course) => (
                  <div key={course.id} className="course-card">
                    <div className="course-header">
                      <h3>{course.code}: {course.title}</h3>
                      <span className={`status-badge ${course.is_full ? 'full' : 'available'}`}>
                        {course.is_full ? 'FULL' : 'Available'}
                      </span>
                    </div>

                    <div className="course-body">
                      <p className="course-description">{course.description}</p>

                      <div className="course-stats">
                        <div className="stat">
                          <span className="stat-label">Students:</span>
                          <span className="stat-value">
                            {course.enrolled_students_count}/{course.max_students}
                          </span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">Available:</span>
                          <span className="stat-value">
                            {course.max_students - course.enrolled_students_count}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="course-actions">
                      <button
                        className="action-btn view-btn"
                        onClick={() => setSelectedCourse(course)}
                      >
                        View Details
                      </button>
                      <button className="action-btn edit-btn">Edit Course</button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-courses-card">
                  <h3>No Courses Assigned</h3>
                  <p>You don't have any courses assigned yet. Contact your administrator to assign courses to you.</p>
                </div>
              )}
            </div>

            {selectedCourse && (
              <div className="course-details-modal">
                <div className="course-details-content">
                  <div className="course-details-header">
                    <h3>{selectedCourse.code}: {selectedCourse.title}</h3>
                    <button
                      className="close-btn"
                      onClick={() => setSelectedCourse(null)}
                    >
                      ×
                    </button>
                  </div>
                  <div className="course-details-body">
                    <div className="course-details-section">
                      <h4>Description</h4>
                      <p>{selectedCourse.description}</p>
                    </div>
                    <div className="course-details-section">
                      <h4>Course Information</h4>
                      <div className="course-info-grid">
                        <div className="info-item">
                          <span className="info-label">Course Code:</span>
                          <span className="info-value">{selectedCourse.code}</span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Max Students:</span>
                          <span className="info-value">{selectedCourse.max_students}</span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Enrolled:</span>
                          <span className="info-value">{selectedCourse.enrolled_students_count}</span>
                        </div>
                        <div className="info-item">
                          <span className="info-label">Status:</span>
                          <span className={`info-value ${selectedCourse.is_full ? 'full' : 'available'}`}>
                            {selectedCourse.is_full ? 'Full' : 'Available'}
                          </span>
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

export default TeacherDashboard;
