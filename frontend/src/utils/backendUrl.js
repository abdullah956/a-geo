/**
 * Utility to get the backend base URL
 * Automatically detects if running on network or localhost
 * Uses the same hostname as the frontend (dynamic - no hardcoded IPs needed)
 */
export const getBackendBaseUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via network IP, use the same IP for backend
  // This way it works with any IP address automatically
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    // Use the same hostname (network IP) for backend
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
 * Automatically uses the same hostname as the frontend (dynamic - no hardcoded IPs needed)
 */
export const getWebSocketUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via network IP, use the same IP for WebSocket
  // This way it works with any IP address automatically
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `ws://${hostname}:8000`;
  }
  
  // Default to localhost for local development
  return 'ws://localhost:8000';
};

