/**
 * WebSocket service for real-time attendance notifications
 */
import { notificationService } from './notificationService';
import { getWebSocketUrl } from '../utils/backendUrl';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000; // 3 seconds
    this.heartbeatInterval = null;
    this.userId = null;
    this.listeners = new Map();
  }

  /**
   * Connect to WebSocket server
   * @param {string} userId - User ID for connection
   */
  async connect(userId) {
    if (this.socket && this.isConnected) {
      console.log('WebSocket already connected');
      return;
    }

    this.userId = userId;
    const token = localStorage.getItem('access');
    
    if (!token) {
      console.error('No access token available for WebSocket connection');
      return;
    }

    try {
      // Get WebSocket URL from utility (already includes protocol)
      const backendBaseUrl = getWebSocketUrl();
      const wsUrl = `${backendBaseUrl}/ws/attendance/notifications/${userId}/`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
      
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket connection open
   */
  handleOpen(event) {
    console.log('WebSocket connected');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    // Send authentication
    this.authenticate();
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Notify listeners
    this.notifyListeners('connected', { connected: true });
  }

  /**
   * Handle WebSocket messages
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('WebSocket message received:', data);
      
      switch (data.type) {
        case 'attendance_session_started':
          this.handleSessionStarted(data);
          break;
        case 'attendance_session_ended':
          this.handleSessionEnded(data);
          break;
        case 'attendance_marked':
          this.handleAttendanceMarked(data);
          break;
        case 'auth_result':
          this.handleAuthResult(data);
          break;
        case 'pong':
          // Heartbeat response
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
      
      // Notify listeners
      this.notifyListeners(data.type, data);
      
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket connection close
   */
  handleClose(event) {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnected = false;
    this.stopHeartbeat();
    
    // Notify listeners
    this.notifyListeners('disconnected', { connected: false });
    
    // Attempt to reconnect if not a normal closure
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket errors
   */
  handleError(error) {
    console.error('WebSocket error:', error);
    this.notifyListeners('error', { error: error.message || 'WebSocket error' });
  }

  /**
   * Authenticate with the WebSocket server
   */
  authenticate() {
    const token = localStorage.getItem('access');
    if (token && this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.send({
        type: 'authenticate',
        token: token
      });
    }
  }

  /**
   * Handle authentication result
   */
  handleAuthResult(data) {
    if (data.authenticated) {
      console.log('WebSocket authentication successful');
    } else {
      console.error('WebSocket authentication failed');
      this.disconnect();
    }
  }

  /**
   * Handle attendance session started
   */
  handleSessionStarted(data) {
    console.log('New attendance session started:', data.session);
    
    // Show browser notification
    if (data.session) {
      notificationService.showAttendanceNotification(data.session);
    }
    
    // Dispatch custom event for other components
    window.dispatchEvent(new CustomEvent('attendance-session-started', {
      detail: data.session
    }));
    
    // Trigger banner refresh
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  }

  /**
   * Handle attendance session ended
   */
  handleSessionEnded(data) {
    console.log('Attendance session ended:', data.session);
    
    // Dispatch custom event for other components
    window.dispatchEvent(new CustomEvent('attendance-session-ended', {
      detail: data.session
    }));
    
    // Trigger banner refresh
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  }

  /**
   * Handle attendance marked
   */
  handleAttendanceMarked(data) {
    console.log('Attendance marked:', data.attendance);
    
    // Show result notification
    if (data.attendance) {
      const success = data.attendance.is_present && data.attendance.status === 'present';
      const message = success 
        ? 'Your attendance has been marked successfully!'
        : 'Your attendance was marked as absent.';
      
      notificationService.showAttendanceResultNotification(success, message);
    }
    
    // Dispatch custom event for other components
    window.dispatchEvent(new CustomEvent('attendance-marked', {
      detail: data.attendance
    }));
    
    // Trigger banner refresh
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  }

  /**
   * Send message through WebSocket
   */
  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, cannot send message:', data);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * this.reconnectAttempts;
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId);
      }
    }, delay);
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.isConnected = false;
    this.stopHeartbeat();
    this.reconnectAttempts = 0;
  }

  /**
   * Add event listener
   */
  addEventListener(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  /**
   * Remove event listener
   */
  removeEventListener(eventType, callback) {
    if (this.listeners.has(eventType)) {
      const callbacks = this.listeners.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Notify all listeners of an event
   */
  notifyListeners(eventType, data) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket listener:', error);
        }
      });
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      readyState: this.socket ? this.socket.readyState : null,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
