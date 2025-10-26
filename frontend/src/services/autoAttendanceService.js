import { attendanceService } from './attendanceService';
import { locationService } from './locationService';
import { notificationService } from './notificationService';
import { sessionMonitorService } from './sessionMonitorService';
import { websocketService } from './websocketService';

/**
 * Automatic attendance service that handles the complete flow
 * from session start to automatic attendance marking
 */

export const autoAttendanceService = {
  isProcessing: false,
  currentSession: null,

  /**
   * Initialize automatic attendance system
   */
  async initialize() {
    // Request notification permission
    await notificationService.requestPermission();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Start WebSocket connection
    this.initializeWebSocket();
    
    // Start session monitoring (as fallback)
    sessionMonitorService.startMonitoring();
    
    // Check for active sessions on page load
    await this.checkActiveSessions();
  },

  /**
   * Initialize WebSocket connection
   */
  initializeWebSocket() {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      if (user && user.id) {
        websocketService.connect(user.id);
        
        // Listen for WebSocket events
        websocketService.addEventListener('attendance_session_started', (data) => {
          this.handleWebSocketSessionStarted(data);
        });
        
        websocketService.addEventListener('attendance_session_ended', (data) => {
          this.handleWebSocketSessionEnded(data);
        });
        
        websocketService.addEventListener('attendance_marked', (data) => {
          this.handleWebSocketAttendanceMarked(data);
        });
        
        console.log('WebSocket initialized for user:', user.id);
      } else {
        console.warn('No user data available for WebSocket connection');
      }
    } catch (error) {
      console.error('Error initializing WebSocket:', error);
    }
  },

  /**
   * Set up event listeners for notifications and session updates
   */
  setupEventListeners() {
    // Listen for attendance session started events (from WebSocket)
    window.addEventListener('attendance-session-started', (event) => {
      this.handleSessionStarted(event.detail);
    });

    // Listen for attendance session ended events (from WebSocket)
    window.addEventListener('attendance-session-ended', (event) => {
      this.handleSessionEnded(event.detail);
    });

    // Listen for refresh attendance banner events
    window.addEventListener('refresh-attendance-banner', () => {
      this.checkActiveSessions();
    });

    // Listen for visibility changes to check for new sessions
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.checkActiveSessions();
      }
    });

    // Listen for focus events
    window.addEventListener('focus', () => {
      this.checkActiveSessions();
    });
  },

  /**
   * Check for active sessions and notify students
   */
  async checkActiveSessions() {
    try {
      console.log('=== CHECKING ACTIVE SESSIONS ===');
      const notifications = await attendanceService.getStudentNotifications();
      console.log('Auto attendance notifications data:', notifications);
      console.log('Active sessions count:', notifications.active_sessions?.length);
      
      if (notifications.active_sessions && notifications.active_sessions.length > 0) {
        console.log('First session details:', notifications.active_sessions[0]);
        console.log('Session has classroom_latitude:', 'classroom_latitude' in notifications.active_sessions[0]);
        console.log('Session has classroom_longitude:', 'classroom_longitude' in notifications.active_sessions[0]);
      }
      
      // Filter out sessions that are already marked and haven't been processed yet
      const unmarkedSessions = notifications.active_sessions.filter(session => 
        !session.attendance_marked && !this.hasProcessedSession(session.id)
      );
      console.log('Auto attendance unmarked sessions:', unmarkedSessions);
      console.log('Unmarked sessions count:', unmarkedSessions.length);

      for (const session of unmarkedSessions) {
        console.log('Processing session:', session.id, session.title);
        await this.handleNewSession(session);
      }
    } catch (error) {
      console.error('Error checking active sessions:', error);
    }
  },

  /**
   * Handle WebSocket session started event
   * @param {Object} data - WebSocket data
   */
  handleWebSocketSessionStarted(data) {
    console.log('WebSocket session started:', data);
    if (data.session) {
      this.handleSessionStarted(data.session);
    }
  },

  /**
   * Handle WebSocket session ended event
   * @param {Object} data - WebSocket data
   */
  handleWebSocketSessionEnded(data) {
    console.log('WebSocket session ended:', data);
    if (data.session) {
      this.handleSessionEnded(data.session);
    }
  },

  /**
   * Handle WebSocket attendance marked event
   * @param {Object} data - WebSocket data
   */
  handleWebSocketAttendanceMarked(data) {
    console.log('WebSocket attendance marked:', data);
    if (data.attendance) {
      this.handleAttendanceMarked(data.attendance);
    }
  },

  /**
   * Handle session started event
   * @param {Object} session - Session data
   */
  handleSessionStarted(session) {
    console.log('=== SESSION STARTED EVENT ===');
    console.log('Session started:', session);
    
    // Check if session has already been processed
    if (this.hasProcessedSession(session.id)) {
      console.log('Session already processed, skipping:', session.id);
      return;
    }
    
    // Mark session as processed (to avoid duplicate notifications)
    this.markSessionAsProcessed(session.id);
    
    // Show notification to user - DON'T automatically mark attendance
    console.log('Showing notification for new session:', session.id);
    
    // Dispatch event to refresh banner (this will show the notification banner)
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  },

  /**
   * Handle session ended event
   * @param {Object} session - Session data
   */
  handleSessionEnded(session) {
    console.log('=== SESSION ENDED EVENT ===');
    console.log('Session ended:', session);
    
    // Dispatch event to refresh banner
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  },

  /**
   * Handle attendance marked event
   * @param {Object} attendance - Attendance data
   */
  handleAttendanceMarked(attendance) {
    console.log('=== ATTENDANCE MARKED EVENT ===');
    console.log('Attendance marked:', attendance);
    
    // Dispatch event to refresh banner
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  },

  /**
   * Handle a new attendance session (legacy method for polling)
   * @param {Object} session - Session data
   */
  async handleNewSession(session) {
    console.log('=== HANDLING NEW SESSION ===');
    console.log('New attendance session detected:', session);
    console.log('Session coordinates check:', {
      hasLat: 'classroom_latitude' in session,
      hasLon: 'classroom_longitude' in session,
      lat: session.classroom_latitude,
      lon: session.classroom_longitude
    });
    
    // Show notification to student
    notificationService.showAttendanceNotification(session);
    
    // Mark session as processed (to avoid duplicate notifications)
    this.markSessionAsProcessed(session.id);
    
    // DON'T automatically mark attendance - let user decide
    console.log('Session notification shown, waiting for user action:', session.id);
    
    // Dispatch event to refresh banner
    window.dispatchEvent(new CustomEvent('refresh-attendance-banner'));
  },

  /**
   * Start automatic attendance marking process
   * @param {Object} session - Session data
   */
  async startAutomaticAttendance(session) {
    if (this.isProcessing) {
      console.log('Already processing attendance, skipping...');
      return;
    }

    this.isProcessing = true;
    this.currentSession = session;

    try {
      console.log('=== STARTING AUTOMATIC ATTENDANCE ===');
      console.log('Starting automatic attendance for session:', session);
      console.log('Session data received:', {
        id: session.id,
        title: session.title,
        classroom_latitude: session.classroom_latitude,
        classroom_longitude: session.classroom_longitude,
        allowed_radius: session.allowed_radius
      });
      
      // Step 1: Request location permission
      console.log('Requesting location permission...');
      const hasLocationPermission = await this.requestLocationPermission();
      console.log('Location permission result:', hasLocationPermission);
      
      if (!hasLocationPermission) {
        console.log('Location permission denied, marking as absent');
        await this.markAbsentDueToNoPermission(session);
        return;
      }

      // Step 2: Get current location
      console.log('Getting current location...');
      const location = await this.getCurrentLocation();
      console.log('Location obtained:', location);
      console.log('Location coordinates:', { lat: location.latitude, lon: location.longitude });
      
      // Step 3: Verify location and mark attendance
      console.log('Verifying location and marking attendance...');
      await this.verifyLocationAndMarkAttendance(session, location);
      
    } catch (error) {
      console.error('Error in automatic attendance:', error);
      this.showErrorModal(`Failed to mark attendance: ${error.message}`);
    } finally {
      this.isProcessing = false;
      this.currentSession = null;
    }
  },

  /**
   * Request location permission with user-friendly prompts
   * @returns {Promise<boolean>}
   */
  async requestLocationPermission() {
    try {
      // Directly try to get location - this will trigger browser permission dialog
      await locationService.getCurrentLocation();
      return true;
    } catch (error) {
      console.error('Error requesting location permission:', error);
      return false;
    }
  },

  /**
   * Get current location with error handling
   * @returns {Promise<Object>}
   */
  async getCurrentLocation() {
    try {
      const location = await locationService.getCurrentLocation();
      return location;
    } catch (error) {
      console.error('Error getting location:', error);
      throw new Error('Unable to get your location. Please ensure location services are enabled.');
    }
  },

  /**
   * Verify location and mark attendance
   * @param {Object} session - Session data
   * @param {Object} location - Student location
   */
  async verifyLocationAndMarkAttendance(session, location) {
    try {
      console.log('=== AUTOMATIC ATTENDANCE DEBUG ===');
      console.log('Session data:', session);
      console.log('Location data:', location);
      console.log('Session classroom coordinates:', { 
        lat: session.classroom_latitude, 
        lon: session.classroom_longitude,
        latType: typeof session.classroom_latitude,
        lonType: typeof session.classroom_longitude
      });
      console.log('Student coordinates:', { 
        lat: location.latitude, 
        lon: location.longitude,
        latType: typeof location.latitude,
        lonType: typeof location.longitude
      });
      console.log('Allowed radius:', session.allowed_radius, 'Type:', typeof session.allowed_radius);
      
      // Validate coordinates before calculation
      if (!session.classroom_latitude || !session.classroom_longitude) {
        console.error('Missing classroom coordinates!', {
          classroom_lat: session.classroom_latitude,
          classroom_lon: session.classroom_longitude
        });
        throw new Error('Classroom coordinates not available');
      }
      
      if (!location.latitude || !location.longitude) {
        console.error('Missing student coordinates!', {
          student_lat: location.latitude,
          student_lon: location.longitude
        });
        throw new Error('Student coordinates not available');
      }
      
      // Calculate distance from classroom
      console.log('Calculating distance...');
      // Convert classroom coordinates to numbers (they come as strings from backend)
      const classroomLat = parseFloat(session.classroom_latitude);
      const classroomLon = parseFloat(session.classroom_longitude);
      console.log('Converted classroom coordinates:', { classroomLat, classroomLon });
      
      const distance = locationService.calculateDistance(
        location.latitude,
        location.longitude,
        classroomLat,
        classroomLon
      );
      
      console.log('Calculated distance:', distance, 'Type:', typeof distance);
      console.log('Distance is finite:', isFinite(distance));
      console.log('Distance is NaN:', isNaN(distance));

      // Check if within allowed radius
      const isWithinRadius = distance <= session.allowed_radius;
      console.log('Is within radius:', isWithinRadius);
      console.log('Distance <= radius:', distance, '<=', session.allowed_radius, '=', distance <= session.allowed_radius);

      if (isWithinRadius) {
        // Mark attendance as present
        const result = await attendanceService.markAttendance(
          session.id,
          location.latitude,
          location.longitude
        );

        if (result.location_verified) {
          notificationService.showAttendanceResultNotification(
            true,
            `Attendance marked successfully! You are ${distance.toFixed(0)}m from the classroom.`
          );
          this.showSuccessModal('Attendance marked successfully!');
          
          // Dispatch event to refresh banner
          window.dispatchEvent(new CustomEvent('attendance-marked', {
            detail: { sessionId: session.id }
          }));
        } else {
          throw new Error('Location verification failed');
        }
      } else {
        // Mark as absent due to location
        await this.markAbsentDueToLocation(session, distance);
      }
    } catch (error) {
      console.error('Error verifying location:', error);
      throw error;
    }
  },

  /**
   * Mark student as absent due to location
   * @param {Object} session - Session data
   * @param {number} distance - Distance from classroom
   */
  async markAbsentDueToLocation(session, distance) {
    try {
      console.log('Marking absent due to location for session:', session.id, 'Distance:', distance);
      
      // Mark attendance as absent
      const result = await attendanceService.markAttendance(
        session.id,
        0, // Invalid coordinates to indicate outside radius
        0
      );

      if (result) {
        const message = `You are ${distance.toFixed(0)}m away from the classroom. Maximum allowed distance is ${session.allowed_radius}m.`;
        
        notificationService.showAttendanceResultNotification(false, message);
        this.showLocationErrorModal(message);
        
        // Dispatch event to refresh banner
        window.dispatchEvent(new CustomEvent('attendance-marked', {
          detail: { sessionId: session.id }
        }));
      }
    } catch (error) {
      console.error('Error marking absent due to location:', error);
      this.showErrorModal('Failed to mark attendance as absent');
    }
  },

  /**
   * Mark student as absent due to no location permission
   * @param {Object} session - Session data
   */
  async markAbsentDueToNoPermission(session) {
    try {
      console.log('Marking absent due to no location permission for session:', session.id);
      
      // Mark attendance as absent
      const result = await attendanceService.markAttendance(
        session.id,
        0, // Invalid coordinates to indicate no location
        0
      );

      if (result) {
        notificationService.showAttendanceResultNotification(
          false,
          'Attendance marked as absent due to location permission denied.'
        );
        this.showSuccessModal('Attendance marked as absent (location permission denied)');
        
        // Dispatch event to refresh banner
        window.dispatchEvent(new CustomEvent('attendance-marked', {
          detail: { sessionId: session.id }
        }));
      }
    } catch (error) {
      console.error('Error marking absent due to no permission:', error);
      this.showErrorModal('Failed to mark attendance as absent');
    }
  },


  /**
   * Show success modal
   * @param {string} message - Success message
   */
  showSuccessModal(message) {
    const modal = document.createElement('div');
    modal.className = 'attendance-success-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-body">
          <div class="success-icon">✅</div>
          <h3>Success!</h3>
          <p>${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" onclick="this.closest('.attendance-success-modal').remove()">
            OK
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Auto-close after 3 seconds
    setTimeout(() => {
      modal.remove();
    }, 3000);
  },

  /**
   * Show error modal
   * @param {string} message - Error message
   */
  showErrorModal(message) {
    const modal = document.createElement('div');
    modal.className = 'attendance-error-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-body">
          <div class="error-icon">❌</div>
          <h3>Error</h3>
          <p>${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" onclick="this.closest('.attendance-error-modal').remove()">
            OK
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  },

  /**
   * Show location error modal
   * @param {string} message - Error message
   */
  showLocationErrorModal(message) {
    const modal = document.createElement('div');
    modal.className = 'location-error-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-body">
          <div class="error-icon">📍</div>
          <h3>Location Verification Failed</h3>
          <p>${message}</p>
          <p><strong>Please move closer to the classroom and try again.</strong></p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" onclick="this.closest('.location-error-modal').remove()">
            Cancel
          </button>
          <button class="btn-primary" onclick="this.retryAttendance()">
            Try Again
          </button>
        </div>
      </div>
    `;

    // Add retry functionality
    modal.querySelector('.btn-primary').onclick = () => {
      modal.remove();
      if (this.currentSession) {
        this.startAutomaticAttendance(this.currentSession);
      }
    };

    document.body.appendChild(modal);
  },

  /**
   * Check if session has been processed
   * @param {number} sessionId - Session ID
   * @returns {boolean}
   */
  hasProcessedSession(sessionId) {
    const processed = localStorage.getItem('processedSessions');
    if (!processed) return false;
    
    const processedSessions = JSON.parse(processed);
    return processedSessions.includes(sessionId);
  },

  /**
   * Mark session as processed
   * @param {number} sessionId - Session ID
   */
  markSessionAsProcessed(sessionId) {
    const processed = localStorage.getItem('processedSessions');
    const processedSessions = processed ? JSON.parse(processed) : [];
    
    if (!processedSessions.includes(sessionId)) {
      processedSessions.push(sessionId);
      localStorage.setItem('processedSessions', JSON.stringify(processedSessions));
    }
  },

  /**
   * Clear processed sessions (useful for testing)
   */
  clearProcessedSessions() {
    localStorage.removeItem('processedSessions');
  }
};
