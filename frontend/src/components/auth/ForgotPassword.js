import React, { useState } from 'react';
import forgotPasswordService from '../../services/forgotPasswordService';
import './AuthForm.css';

const ForgotPassword = ({ onBack, onSuccess }) => {
  const [step, setStep] = useState(1); // 1: Email, 2: OTP, 3: New Password
  const [formData, setFormData] = useState({
    email: '',
    otp: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleStep1 = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await forgotPasswordService.requestPasswordReset(formData.email);
      setMessage(response.message);
      setStep(2);
    } catch (error) {
      setError(error.error || error.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleStep2 = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await forgotPasswordService.verifyOTP(formData.email, formData.otp);
      setMessage(response.message);
      setStep(3);
    } catch (error) {
      setError(error.error || error.message || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleStep3 = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (formData.newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      setLoading(false);
      return;
    }

    try {
      const response = await forgotPasswordService.resetPassword(
        formData.email, 
        formData.otp, 
        formData.newPassword
      );
      setMessage(response.message);
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (error) {
      setError(error.error || error.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="auth-form-container">
      <div className="auth-form">
        <h2>Reset Password</h2>
        <p className="auth-description">
          Enter your email address and we'll send you an OTP to reset your password.
        </p>
        
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}

        <form onSubmit={handleStep1}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
        </form>

        <div className="auth-footer">
          <button type="button" className="switch-btn" onClick={onBack}>
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="auth-form-container">
      <div className="auth-form">
        <h2>Verify OTP</h2>
        <p className="auth-description">
          We've sent a 6-digit OTP to <strong>{formData.email}</strong>. 
          Please enter it below.
        </p>
        
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}

        <form onSubmit={handleStep2}>
          <div className="form-group">
            <label htmlFor="otp">OTP Code</label>
            <input
              type="text"
              id="otp"
              name="otp"
              value={formData.otp}
              onChange={handleInputChange}
              required
              placeholder="Enter 6-digit OTP"
              maxLength="6"
              pattern="[0-9]{6}"
            />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>

        <div className="auth-footer">
          <button type="button" className="switch-btn" onClick={() => setStep(1)}>
            Change Email
          </button>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="auth-form-container">
      <div className="auth-form">
        <h2>Set New Password</h2>
        <p className="auth-description">
          Enter your new password below.
        </p>
        
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}

        <form onSubmit={handleStep3}>
          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              type="password"
              id="newPassword"
              name="newPassword"
              value={formData.newPassword}
              onChange={handleInputChange}
              required
              placeholder="Enter new password"
              minLength="8"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
              placeholder="Confirm new password"
              minLength="8"
            />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <div className="auth-footer">
          <button type="button" className="switch-btn" onClick={() => setStep(2)}>
            Back to OTP
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {step === 1 && renderStep1()}
      {step === 2 && renderStep2()}
      {step === 3 && renderStep3()}
    </>
  );
};

export default ForgotPassword;
