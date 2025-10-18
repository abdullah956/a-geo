/**
 * Notification service for real-time attendance alerts
 */

export const notificationService = {
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

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  },

  /**
   * Show attendance session notification
   * @param {Object} session - Attendance session data
   */
  showAttendanceNotification: (session) => {
    if (Notification.permission !== 'granted') {
      return;
    }

    const notification = new Notification('Attendance Session Started', {
      body: `${session.title} - ${session.course_code}\nClassroom: ${session.classroom_name}\nClick to mark your attendance`,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: `attendance-${session.id}`,
      requireInteraction: true,
      actions: [
        {
          action: 'mark-attendance',
          title: 'Mark Attendance'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
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
  },


  /**
   * Show attendance result notification
   * @param {boolean} success - Whether attendance was marked successfully
   * @param {string} message - Result message
   */
  showAttendanceResultNotification: (success, message) => {
    if (Notification.permission !== 'granted') {
      return;
    }

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
    return Notification.permission;
  }
};
