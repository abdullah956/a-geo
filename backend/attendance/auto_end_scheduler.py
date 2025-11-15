"""
Background scheduler to automatically end expired attendance sessions
This module is automatically started when Django loads the attendance app.
"""
import time
import logging
import threading
from datetime import timedelta
from django.utils import timezone
from attendance.models import AttendanceSession
from attendance.websocket_service import websocket_service

logger = logging.getLogger('attendance')


def auto_end_expired_sessions():
    """
    Check for and end sessions that have exceeded their scheduled duration
    """
    try:
        # Check database connection
        from django.db import connection
        try:
            connection.ensure_connection()
        except Exception as db_error:
            logger.warning(f'Database connection issue (will retry): {db_error}')
            return 0
        
        # Get all active sessions
        active_sessions = AttendanceSession.objects.filter(status='active')
        
        if not active_sessions.exists():
            return 0
        
        ended_count = 0
        current_time = timezone.now()
        
        for session in active_sessions:
            try:
                # Calculate when the session should end
                scheduled_end_time = session.started_at + timedelta(minutes=session.scheduled_duration)
                
                # Debug logging for timezone-aware comparison
                logger.debug(
                    f'Session {session.id}: started_at={session.started_at} (tz-aware: {session.started_at.tzinfo}), '
                    f'duration={session.scheduled_duration}min, scheduled_end={scheduled_end_time}, '
                    f'current_time={current_time} (tz-aware: {current_time.tzinfo})'
                )
                
                # Check if current time is past the scheduled end time
                if current_time >= scheduled_end_time:
                    logger.info(
                        f'Ending expired session: {session.title} (ID: {session.id}). '
                        f'Started: {session.started_at}, Duration: {session.scheduled_duration} min, '
                        f'Scheduled end: {scheduled_end_time}, Current time: {current_time}'
                    )
                    
                    # End the session
                    session.end_session()
                    
                    # Send WebSocket notification to enrolled students
                    try:
                        enrolled_students = session.course.enrollments.filter(
                            is_active=True
                        ).values_list('student_id', flat=True)
                        websocket_service.send_session_ended_notification(
                            session, list(enrolled_students)
                        )
                        logger.info(
                            f'Sent session ended notification for session {session.id} '
                            f'to {len(enrolled_students)} students'
                        )
                    except Exception as e:
                        logger.error(
                            f'Failed to send WebSocket notification for session {session.id}: {e}',
                            exc_info=True
                        )
                    
                    logger.info(
                        f'Auto-ended session {session.id} - {session.title} '
                        f'at {timezone.now()}'
                    )
                    
                    ended_count += 1
            except Exception as e:
                logger.error(
                    f'Error ending session {session.id}: {e}',
                    exc_info=True
                )
        
        if ended_count > 0:
            logger.info(f'Auto-ended {ended_count} session(s) at {timezone.now()}')
        
        return ended_count
        
    except Exception as e:
        logger.error(
            f'Error in auto_end_expired_sessions: {e}',
            exc_info=True
        )
        return 0


def run_scheduler(check_interval=60):
    """
    Run the scheduler that checks for expired sessions every check_interval seconds
    
    Args:
        check_interval (int): Seconds between checks (default: 60)
    """
    global _scheduler_running
    
    logger.info(
        f'Starting auto-end scheduler (checking every {check_interval} seconds)...'
    )
    print(f'[SCHEDULER] Starting auto-end scheduler (checking every {check_interval} seconds)...')
    
    # Run initial check immediately
    try:
        print('[SCHEDULER] Running initial check for expired sessions...')
        ended = auto_end_expired_sessions()
        if ended > 0:
            logger.info(f'Initial check: ended {ended} expired session(s)')
            print(f'[SCHEDULER] Initial check: ended {ended} expired session(s)')
        else:
            print('[SCHEDULER] Initial check: no expired sessions found')
    except Exception as e:
        logger.error(f'Error in initial scheduler check: {e}', exc_info=True)
        print(f'[SCHEDULER] ✗ Error in initial check: {e}')
        import traceback
        traceback.print_exc()
    
    # Then run periodic checks
    try:
        while _scheduler_running:
            time.sleep(check_interval)
            if _scheduler_running:  # Check again after sleep
                auto_end_expired_sessions()
    except Exception as e:
        logger.error(f'Scheduler stopped due to error: {e}', exc_info=True)
    finally:
        _scheduler_running = False
        logger.info('Scheduler thread stopped')


# Global variable to track if scheduler is running
_scheduler_thread = None
_scheduler_running = False


def start_scheduler_thread(check_interval=60):
    """
    Start the scheduler in a background thread
    
    Args:
        check_interval (int): Seconds between checks (default: 60)
    """
    global _scheduler_thread, _scheduler_running
    
    # Check if scheduler is already running and thread is alive
    if _scheduler_running and _scheduler_thread is not None:
        if _scheduler_thread.is_alive():
            logger.warning('Scheduler is already running and thread is alive')
            print('[SCHEDULER] Already running - skipping start')
            return
        else:
            # Thread died, reset flag and start new one
            logger.warning('Scheduler thread died, restarting...')
            print('[SCHEDULER] Thread died, restarting...')
            _scheduler_running = False
    
    try:
        _scheduler_running = True
        _scheduler_thread = threading.Thread(
            target=run_scheduler,
            args=(check_interval,),
            daemon=True,
            name='AttendanceAutoEndScheduler'
        )
        _scheduler_thread.start()
        logger.info('Auto-end scheduler thread started successfully')
        print('[SCHEDULER] ✓ Auto-end scheduler thread started successfully')
        print(f'[SCHEDULER] Checking every {check_interval} seconds')
    except Exception as e:
        _scheduler_running = False
        logger.error(f'Failed to start scheduler thread: {e}', exc_info=True)
        print(f'[SCHEDULER] ✗ Failed to start: {e}')
        raise  # Re-raise so we can see the error


def stop_scheduler():
    """Stop the scheduler (for testing purposes)"""
    global _scheduler_running
    _scheduler_running = False
    logger.info('Scheduler stop requested')


if __name__ == '__main__':
    # Allow running as standalone script for testing
    import os
    import sys
    import django
    
    # Setup Django
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    run_scheduler(check_interval=60)  # Check every minute
