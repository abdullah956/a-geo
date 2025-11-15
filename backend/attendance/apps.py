from django.apps import AppConfig
import logging

logger = logging.getLogger('attendance')


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Attendance Management'
    
    def ready(self):
        """
        Start the auto-end scheduler when Django is ready.
        This ensures the scheduler runs regardless of whether we're using ASGI or WSGI.
        """
        # Don't start scheduler during migrations or other management commands
        import sys
        if len(sys.argv) > 1 and any(cmd in sys.argv[1:] for cmd in ['migrate', 'makemigrations', 'test', 'shell', 'shell_plus']):
            return
        
        # Prevent multiple starts in development auto-reload
        # Use a flag to ensure we only start once per process
        if not hasattr(self, '_scheduler_started'):
            self._scheduler_started = True
        else:
            # Already started in this process
            return
        
        # Import here to avoid circular imports
        try:
            from attendance.auto_end_scheduler import start_scheduler_thread
            # Start scheduler with 60 second check interval
            print('[ATTENDANCE APP] Starting auto-end scheduler...')
            start_scheduler_thread(check_interval=60)
            logger.info('Attendance app ready - auto-end scheduler started')
            print('[ATTENDANCE APP] ✓ Auto-end scheduler initialization complete')
        except Exception as e:
            logger.error(f'Failed to start auto-end scheduler in AppConfig: {e}', exc_info=True)
            print(f'[ATTENDANCE APP] ✗ Failed to start scheduler: {e}')
            import traceback
            traceback.print_exc()
