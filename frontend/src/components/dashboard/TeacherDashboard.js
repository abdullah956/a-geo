import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import './Dashboard.css';

const TeacherDashboard = () => {
  const [user, setUser] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

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
          <p>Teacher Dashboard</p>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-welcome">
          <h2>{dashboardData?.message}</h2>
          <p>You are logged in as a Teacher</p>
        </div>

        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h3>Manage Courses</h3>
            <p>Create and manage your courses</p>
            <button className="card-btn">Manage Courses</button>
          </div>

          <div className="dashboard-card">
            <h3>Grade Assignments</h3>
            <p>Review and grade student assignments</p>
            <button className="card-btn">Grade Assignments</button>
          </div>

          <div className="dashboard-card">
            <h3>View Students</h3>
            <p>Monitor student progress and performance</p>
            <button className="card-btn">View Students</button>
          </div>

          <div className="dashboard-card">
            <h3>Analytics</h3>
            <p>View teaching analytics and reports</p>
            <button className="card-btn">View Analytics</button>
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
      </main>
    </div>
  );
};

export default TeacherDashboard;
