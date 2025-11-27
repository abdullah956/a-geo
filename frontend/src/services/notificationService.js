/**
 * Notification service for real-time attendance alerts
 * Note: Mobile browsers require Service Workers for notifications
 * This service gracefully falls back when direct notifications aren't supported
 */

export const notificationService = {
  /**
   * Check if direct Notification constructor is supported
   * Mobile browsers don't support new Notification() directly
   */
  isDirectNotificationSupported: () => {
    if (!('Notification' in window)) {
      return false;
    }
    
    // Try to check if Notification constructor works
    // Mobile browsers throw "Illegal constructor" error
    try {
      // This is a feature detection - we don't actually create the notification
      return typeof Notification === 'function';
    } catch (e) {
      return false;
    }
  },

  /**
   * Request notification permission from user
   * @returns {Promise<boolean>}
   */
  requestPermission: async () => {
    if (!('Notification' in window)) {
      console.log('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission === 'denied') {
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    } catch (e) {
      console.log('Notification permission request failed:', e);
      return false;
    }
  },

  /**
   * Show attendance session notification
   * @param {Object} session - Attendance session data
   */
  showAttendanceNotification: (session) => {
    if (Notification.permission !== 'granted') {
      return null;
    }

    try {
      const notification = new Notification('Attendance Session Started', {
        body: `${session.title} - ${session.course_code}\nClassroom: ${session.classroom_name}\nClick to mark your attendance`,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: `attendance-${session.id}`,
        requireInteraction: true
      });

      notification.onclick = () => {
        window.focus();
        // Trigger attendance marking flow
        window.dispatchEvent(new CustomEvent('attendance-session-started', {
          detail: session
        }));
        notification.close();
      };

      // Auto-close after 30 seconds
      setTimeout(() => {
        notification.close();
      }, 30000);

      return notification;
    } catch (e) {
      // Mobile browsers don't support direct Notification constructor
      console.log('Direct notifications not supported on this device:', e.message);
      return null;
    }
  },


  /**
   * Show attendance result notification
   * @param {boolean} success - Whether attendance was marked successfully
   * @param {string} message - Result message
   */
  showAttendanceResultNotification: (success, message) => {
    if (Notification.permission !== 'granted') {
      return null;
    }

    try {
      const notification = new Notification(
        success ? 'Attendance Marked Successfully' : 'Attendance Failed',
        {
          body: message,
          icon: '/favicon.ico',
          tag: 'attendance-result'
        }
      );

      setTimeout(() => {
        notification.close();
      }, 5000);

      return notification;
    } catch (e) {
      // Mobile browsers don't support direct Notification constructor
      console.log('Direct notifications not supported on this device:', e.message);
      return null;
    }
  },

  /**
   * Check if notifications are supported and enabled
   * @returns {boolean}
   */
  isSupported: () => {
    return 'Notification' in window;
  },

  /**
   * Get current notification permission status
   * @returns {string}
   */
  getPermissionStatus: () => {
    if (!('Notification' in window)) {
      return 'unsupported';
    }
    return Notification.permission;
  }
};
