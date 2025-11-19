import React, { useState, useEffect, useCallback } from 'react';
import { qrCodeService } from '../../services/qrCodeService';
import './QRCodeDisplay.css';

const QRCodeDisplay = ({ session, onClose }) => {
  const [qrData, setQrData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const generateQRCode = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await qrCodeService.generateToken(session.id, 10);
      setQrData(data);
    } catch (err) {
      setError(err.error || 'Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  }, [session.id]);

  const handleRefresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await qrCodeService.refreshToken(session.id, qrData?.token);
      setQrData(data);
    } catch (err) {
      setError(err.error || 'Failed to refresh QR code');
    } finally {
      setLoading(false);
    }
  }, [session.id, qrData?.token]);

  useEffect(() => {
    generateQRCode();
  }, [generateQRCode]);

  useEffect(() => {
    if (!qrData) return;

    // Update countdown timer
    const timer = setInterval(() => {
      const now = new Date();
      const expiresAt = new Date(qrData.expires_at);
      const diff = expiresAt - now;

      if (diff <= 0) {
        setTimeRemaining(0);
        if (autoRefresh) {
          handleRefresh();
        }
      } else {
        setTimeRemaining(Math.floor(diff / 1000));
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [qrData, autoRefresh, handleRefresh]);

  const formatTime = useCallback((seconds) => {
    if (seconds === null) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  const getTimerColor = useCallback(() => {
    if (timeRemaining === null) return '';
    if (timeRemaining <= 60) return 'timer-critical';
    if (timeRemaining <= 180) return 'timer-warning';
    return 'timer-ok';
  }, [timeRemaining]);

  return (
    <div className="qr-code-modal-overlay">
      <div className="qr-code-modal">
        <div className="qr-code-header">
          <h2>📱 QR Code Attendance</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <div className="qr-code-content">
          <div className="session-info">
            <h3>{session.title}</h3>
            <p className="course-code">{session.course_code}</p>
            <p className="classroom-name">{session.classroom_name}</p>
          </div>

          {loading && !qrData && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Generating QR Code...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <p className="error-message">⚠️ {error}</p>
              <button onClick={generateQRCode} className="retry-btn">
                Try Again
              </button>
            </div>
          )}

          {qrData && !loading && (
            <>
              <div className="qr-code-container">
                <img 
                  src={qrData.qr_code} 
                  alt="Attendance QR Code" 
                  className="qr-code-image"
                />
                <div className={`timer-display ${getTimerColor()}`}>
                  <span className="timer-label">Expires in:</span>
                  <span className="timer-value">{formatTime(timeRemaining)}</span>
                </div>
              </div>

              <div className="qr-code-instructions">
                <h4>Instructions for Students:</h4>
                <ol>
                  <li>Open your mobile camera or QR code scanner</li>
                  <li>Scan this QR code</li>
                  <li>You will be taken to the LMS login page</li>
                  <li>Login with your credentials</li>
                  <li>Your attendance will be marked automatically!</li>
                </ol>
              </div>

              <div className="qr-code-actions">
                <label className="auto-refresh-toggle">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                  />
                  <span>Auto-refresh when expired</span>
                </label>

                <button 
                  onClick={handleRefresh} 
                  className="refresh-btn"
                  disabled={loading}
                >
                  🔄 Refresh QR Code
                </button>
              </div>

              <div className="token-info">
                <p className="token-id">Token ID: #{qrData.token_id}</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default QRCodeDisplay;

