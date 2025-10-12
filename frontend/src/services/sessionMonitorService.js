import { attendanceService } from './attendanceService';
import { autoAttendanceService } from './autoAttendanceService';

/**
 * Session monitoring service that checks for new attendance sessions
 * and triggers automatic attendance flow
 */

export const sessionMonitorService = {
  isMonitoring: false,
  checkInterval: null,
  lastCheckTime: null,

  /**
   * Start monitoring for new attendance sessions
   * @param {number} intervalMs - Check interval in milliseconds (default: 30 seconds)
   */
  startMonitoring(intervalMs = 30000) {
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;
    this.lastCheckTime = new Date();

    console.log('Starting session monitoring...');

    // Check immediately
    this.checkForNewSessions();

    // Set up periodic checking
    this.checkInterval = setInterval(() => {
      this.checkForNewSessions();
    }, intervalMs);

    // Also check when page becomes visible
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.checkForNewSessions();
      }
    });

    // Check when window gains focus
    window.addEventListener('focus', () => {
      this.checkForNewSessions();
    });
  },

  /**
   * Stop monitoring for new sessions
   */
  stopMonitoring() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.isMonitoring = false;
    console.log('Session monitoring stopped');
  },

  /**
   * Check for new attendance sessions
   */
  async checkForNewSessions() {
    try {
      const notifications = await attendanceService.getStudentNotifications();
      
      // Get unmarked sessions
      const unmarkedSessions = notifications.active_sessions.filter(session => 
        !session.attendance_marked && !this.hasProcessedSession(session.id)
      );

      if (unmarkedSessions.length > 0) {
        console.log(`Found ${unmarkedSessions.length} new attendance session(s)`);
        
        for (const session of unmarkedSessions) {
          await this.handleNewSession(session);
        }
      }

      this.lastCheckTime = new Date();
    } catch (error) {
      console.error('Error checking for new sessions:', error);
    }
  },

  /**
   * Handle a new attendance session
   * @param {Object} session - Session data
   */
  async handleNewSession(session) {
    console.log('Handling new session:', session);
    
    // Mark session as processed
    this.markSessionAsProcessed(session.id);
    
    // Trigger automatic attendance flow
    await autoAttendanceService.handleNewSession(session);
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
   * Get monitoring status
   * @returns {Object}
   */
  getStatus() {
    return {
      isMonitoring: this.isMonitoring,
      lastCheckTime: this.lastCheckTime,
      checkInterval: this.checkInterval
    };
  },

  /**
   * Clear processed sessions (useful for testing)
   */
  clearProcessedSessions() {
    localStorage.removeItem('processedSessions');
    console.log('Processed sessions cleared');
  }
};
