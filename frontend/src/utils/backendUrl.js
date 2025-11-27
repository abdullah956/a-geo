/**
 * Utility to get the backend base URL
 * Automatically detects if running on network, localhost, or ngrok
 */

// Network IP for backend when using ngrok
// Set via REACT_APP_NETWORK_IP in .env file or defaults to auto-detect
const NETWORK_IP = process.env.REACT_APP_NETWORK_IP || null;

export const getBackendBaseUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via ngrok (HTTPS tunnel for mobile geolocation)
  if (hostname.includes('ngrok')) {
    // If NETWORK_IP is set in .env, use it
    if (NETWORK_IP) {
      return `http://${NETWORK_IP}:8000`;
    }
    // Otherwise, try to get from localStorage (can be set manually)
    const savedIP = localStorage.getItem('BACKEND_NETWORK_IP');
    if (savedIP) {
      return `http://${savedIP}:8000`;
    }
    // Fallback error - user needs to set the IP
    console.error('NETWORK_IP not configured! Set REACT_APP_NETWORK_IP in .env or call setBackendIP()');
    return 'http://localhost:8000';
  }
  
  // If accessing via network IP, use the same IP for backend
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `http://${hostname}:8000`;
  }
  
  // Default to localhost for local development
  return 'http://localhost:8000';
};

/**
 * Get the API base URL
 */
export const getApiBaseUrl = () => {
  return `${getBackendBaseUrl()}/api`;
};

/**
 * Get the WebSocket URL
 */
export const getWebSocketUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via ngrok, use network IP for WebSocket
  if (hostname.includes('ngrok')) {
    if (NETWORK_IP) {
      return `ws://${NETWORK_IP}:8000`;
    }
    const savedIP = localStorage.getItem('BACKEND_NETWORK_IP');
    if (savedIP) {
      return `ws://${savedIP}:8000`;
    }
    return 'ws://localhost:8000';
  }
  
  // If accessing via network IP, use the same IP for WebSocket
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `ws://${hostname}:8000`;
  }
  
  // Default to localhost for local development
  return 'ws://localhost:8000';
};

/**
 * Set backend IP manually (useful when accessed via ngrok)
 * This saves to localStorage so it persists
 */
export const setBackendIP = (ip) => {
  localStorage.setItem('BACKEND_NETWORK_IP', ip);
  console.log(`Backend IP set to: ${ip}`);
  // Reload to apply changes
  window.location.reload();
};

/**
 * Get the currently configured backend IP
 */
export const getBackendIP = () => {
  return NETWORK_IP || localStorage.getItem('BACKEND_NETWORK_IP') || 'Not configured';
};
