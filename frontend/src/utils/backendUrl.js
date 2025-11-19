/**
 * Utility to get the backend base URL
 * Automatically detects if running on network or localhost
 */
export const getBackendBaseUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via network IP, use network IP for backend
  if (hostname === '192.168.18.13' || hostname === '192.168.18.12' || (hostname !== 'localhost' && hostname !== '127.0.0.1')) {
    // Use the computer's network IP (where backend is running)
    return 'http://192.168.18.13:8000';
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
  
  // If accessing via network IP, use network IP for WebSocket
  if (hostname === '192.168.18.13' || hostname === '192.168.18.12' || (hostname !== 'localhost' && hostname !== '127.0.0.1')) {
    return 'ws://192.168.18.13:8000';
  }
  
  // Default to localhost for local development
  return 'ws://localhost:8000';
};

