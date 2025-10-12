import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import './Dashboard.css';

const AdminDashboard = () => {
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
          <p>Admin Dashboard</p>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-welcome">
          <h2>{dashboardData?.message}</h2>
          <p>You are logged in as an Admin</p>
        </div>

        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h3>Manage Users</h3>
            <p>Add, edit, and manage user accounts</p>
            <button className="card-btn">Manage Users</button>
          </div>

          <div className="dashboard-card">
            <h3>System Settings</h3>
            <p>Configure system-wide settings</p>
            <button className="card-btn">System Settings</button>
          </div>

          <div className="dashboard-card">
            <h3>Analytics</h3>
            <p>View comprehensive system analytics</p>
            <button className="card-btn">View Analytics</button>
          </div>

          <div className="dashboard-card">
            <h3>Reports</h3>
            <p>Generate and view system reports</p>
            <button className="card-btn">Generate Reports</button>
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

export default AdminDashboard;
