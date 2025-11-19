import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { qrCodeService } from '../../services/qrCodeService';
import { locationService } from '../../services/locationService';
import LoginForm from '../auth/LoginForm';
import './QRCodeAttendance.css';

const QRCodeAttendance = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('processing'); // processing, login, success, error
  const [message, setMessage] = useState('');
  const [sessionInfo, setSessionInfo] = useState(null);

  const markAttendanceWithToken = useCallback(async () => {
    try {
      setMessage('Getting your location...');
      
      // Get user's location
      let latitude = 0;
      let longitude = 0;
      
      try {
        const location = await locationService.getCurrentLocation();
        latitude = location.latitude;
        longitude = location.longitude;
      } catch (locationError) {
        console.warn('Location access denied or unavailable:', locationError);
        // Continue without location (will be handled by backend)
      }

      setMessage('Marking your attendance...');

      // Verify token and mark attendance
      const result = await qrCodeService.verifyToken(token, latitude, longitude);
      
      if (result.attendance) {
        setStatus('success');
        setMessage('✅ Your attendance has been marked successfully!');
        setSessionInfo({
          sessionTitle: result.session?.title || 'Attendance Session',
          courseCode: result.session?.course_code || 'N/A',
          status: result.attendance.status
        });

        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
          navigate('/dashboard');
        }, 3000);
      } else {
        setStatus('error');
        setMessage('Failed to mark attendance. Please try again.');
      }
    } catch (error) {
      console.error('Error marking attendance:', error);
      setStatus('error');
      setMessage(error.response?.data?.error || error.message || 'Failed to mark attendance');
    }
  }, [token, navigate]);

  const handleQRCodeToken = useCallback(async () => {
    try {
      setLoading(true);
      setStatus('processing');
      setMessage('Processing QR code...');

      // Check if user is authenticated
      const isAuthenticated = authService.isAuthenticated();
      
      if (!isAuthenticated) {
        // User not logged in - redirect to login
        setStatus('login');
        setMessage('Please login to mark your attendance');
        return;
      }

      // User is logged in - mark attendance
      await markAttendanceWithToken();
      
    } catch (error) {
      console.error('Error processing QR code:', error);
      setStatus('error');
      setMessage(error.response?.data?.error || error.message || 'Failed to process QR code');
    } finally {
      setLoading(false);
    }
  }, [markAttendanceWithToken]);

  useEffect(() => {
    handleQRCodeToken();
  }, [handleQRCodeToken]);

  const handleLoginSuccess = useCallback(async () => {
    // After successful login, update auth state and mark attendance
    // Force a small delay to ensure auth state is updated
    setTimeout(async () => {
      await markAttendanceWithToken();
    }, 500);
  }, [markAttendanceWithToken]);

  if (status === 'login') {
    return (
      <div className="qr-attendance-container">
        <div className="qr-attendance-card">
          <div className="qr-attendance-header">
            <h2>📱 QR Code Attendance</h2>
            <p>Please login to mark your attendance</p>
          </div>
          <div className="qr-attendance-login">
            <LoginForm 
              onSwitchToRegister={() => navigate('/register')}
              onLoginSuccess={handleLoginSuccess}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="qr-attendance-container">
      <div className="qr-attendance-card">
        {loading && (
          <div className="qr-attendance-loading">
            <div className="spinner"></div>
            <p>{message}</p>
          </div>
        )}

        {status === 'success' && (
          <div className="qr-attendance-success">
            <div className="success-icon">✅</div>
            <h2>Attendance Marked!</h2>
            <p className="success-message">{message}</p>
            {sessionInfo && (
              <div className="session-info">
                <p><strong>Session:</strong> {sessionInfo.sessionTitle}</p>
                <p><strong>Course:</strong> {sessionInfo.courseCode}</p>
                <p><strong>Status:</strong> {sessionInfo.status}</p>
              </div>
            )}
            <p className="redirect-message">Redirecting to dashboard...</p>
            <button 
              onClick={() => navigate('/dashboard')}
              className="go-to-dashboard-btn"
            >
              Go to Dashboard
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="qr-attendance-error">
            <div className="error-icon">❌</div>
            <h2>Error</h2>
            <p className="error-message">{message}</p>
            <div className="error-actions">
              <button 
                onClick={() => window.location.reload()}
                className="retry-btn"
              >
                Try Again
              </button>
              <button 
                onClick={() => navigate('/dashboard')}
                className="go-to-dashboard-btn"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        )}

        {status === 'processing' && !loading && (
          <div className="qr-attendance-processing">
            <div className="spinner"></div>
            <p>{message}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QRCodeAttendance;

