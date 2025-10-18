import React, { useState } from 'react';
import { qrCodeService } from '../../services/qrCodeService';
import { locationService } from '../../services/locationService';
import './QRCodeScanner.css';

const QRCodeScanner = ({ onClose, onSuccess }) => {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!token.trim()) {
      setError('Please enter a token');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Try to get location (optional)
      let latitude = null;
      let longitude = null;

      try {
        const location = await locationService.getCurrentLocation();
        latitude = location.latitude;
        longitude = location.longitude;
      } catch (locError) {
        console.log('Location not available, proceeding without it');
      }

      // Verify token and mark attendance
      const result = await qrCodeService.verifyToken(token.trim(), latitude, longitude);
      
      setSuccess(`Attendance marked successfully for ${result.session.course_code}!`);
      
      // Call success callback after a short delay
      setTimeout(() => {
        if (onSuccess) {
          onSuccess(result);
        }
        onClose();
      }, 2000);

    } catch (err) {
      setError(err.error || 'Failed to verify token');
    } finally {
      setLoading(false);
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setToken(text.trim());
    } catch (err) {
      setError('Failed to read from clipboard');
    }
  };

  return (
    <div className="qr-scanner-modal-overlay">
      <div className="qr-scanner-modal">
        <div className="qr-scanner-header">
          <h2>📱 Scan QR Code</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <div className="qr-scanner-content">
          <div className="scanner-instructions">
            <p>Enter the token from the QR code displayed by your teacher</p>
          </div>

          <form onSubmit={handleSubmit} className="token-form">
            <div className="input-group">
              <label htmlFor="token-input">Token:</label>
              <div className="input-with-button">
                <textarea
                  id="token-input"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste or type the token here..."
                  rows="4"
                  disabled={loading || success}
                  className="token-input"
                />
                <button
                  type="button"
                  onClick={handlePaste}
                  className="paste-btn"
                  disabled={loading || success}
                  title="Paste from clipboard"
                >
                  📋 Paste
                </button>
              </div>
            </div>

            {error && (
              <div className="error-message">
                ⚠️ {error}
              </div>
            )}

            {success && (
              <div className="success-message">
                ✅ {success}
              </div>
            )}

            <div className="scanner-actions">
              <button
                type="button"
                onClick={onClose}
                className="cancel-btn"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="submit-btn"
                disabled={loading || success || !token.trim()}
              >
                {loading ? 'Verifying...' : success ? 'Success!' : 'Mark Attendance'}
              </button>
            </div>
          </form>

          <div className="scanner-help">
            <h4>How to use:</h4>
            <ol>
              <li>Ask your teacher to display the QR code</li>
              <li>Copy the token text from the QR code</li>
              <li>Paste it in the field above</li>
              <li>Click "Mark Attendance"</li>
            </ol>
            <p className="help-note">
              💡 Tip: You can also manually type the token if needed
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRCodeScanner;

