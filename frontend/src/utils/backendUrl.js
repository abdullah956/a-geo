/**
 * Utility to get the backend base URL
 * Automatically detects if running on network, localhost, or ngrok
 */

// Network IP for backend when using ngrok (ngrok only tunnels frontend)
// Update this to your current network IP
const NETWORK_IP = '192.168.18.29';

export const getBackendBaseUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via ngrok (HTTPS tunnel for mobile geolocation)
  // Use the network IP for backend since ngrok only tunnels frontend
  if (hostname.includes('ngrok')) {
    return `http://${NETWORK_IP}:8000`;
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
 * Automatically uses the same hostname as the frontend
 */
export const getWebSocketUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via ngrok, use network IP for WebSocket
  if (hostname.includes('ngrok')) {
    return `ws://${NETWORK_IP}:8000`;
  }
  
  // If accessing via network IP, use the same IP for WebSocket
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `ws://${hostname}:8000`;
  }
  
  // Default to localhost for local development
  return 'ws://localhost:8000';
};
