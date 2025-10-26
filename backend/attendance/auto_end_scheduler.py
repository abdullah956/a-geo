"""
Background scheduler to automatically end expired attendance sessions
Run this script alongside your Django server:
    python manage.py runscript auto_end_scheduler (if using django-extensions)
    OR
    python attendance/auto_end_scheduler.py
"""
import os
import sys
import django
import time
import logging
from datetime import timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from attendance.models import AttendanceSession
from attendance.websocket_service import websocket_service

logger = logging.getLogger(__name__)


def auto_end_expired_sessions():
    """
    Check for and end sessions that have exceeded their scheduled duration
    """
    try:
        # Get all active sessions
        active_sessions = AttendanceSession.objects.filter(status='active')
        
        ended_count = 0
        
        for session in active_sessions:
            # Calculate when the session should end
            scheduled_end_time = session.started_at + timedelta(minutes=session.scheduled_duration)
            
            # Check if current time is past the scheduled end time
            if timezone.now() >= scheduled_end_time:
                # End the session
                session.end_session()
                
                # Send WebSocket notification to enrolled students
                try:
                    enrolled_students = session.course.enrollments.filter(is_active=True).values_list('student_id', flat=True)
                    websocket_service.send_session_ended_notification(session, list(enrolled_students))
                    logger.info(f'Sent session ended notification for session {session.id} to {len(enrolled_students)} students')
                except Exception as e:
                    logger.error(f'Failed to send WebSocket notification: {e}')
                
                print(f'[{timezone.now()}] Auto-ended session: {session.title} (ID: {session.id})')
                logger.info(f'Auto-ended session {session.id} - {session.title}')
                
                ended_count += 1
        
        if ended_count > 0:
            print(f'[{timezone.now()}] Ended {ended_count} session(s)')
        
    except Exception as e:
        logger.error(f'Error in auto_end_expired_sessions: {e}')
        print(f'[{timezone.now()}] Error: {e}')


def run_scheduler(check_interval=60):
    """
    Run the scheduler that checks for expired sessions every check_interval seconds
    
    Args:
        check_interval (int): Seconds between checks (default: 60)
    """
    print(f'Starting auto-end scheduler (checking every {check_interval} seconds)...')
    print('Press Ctrl+C to stop')
    
    try:
        while True:
            auto_end_expired_sessions()
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print('\nScheduler stopped')


if __name__ == '__main__':
    run_scheduler(check_interval=60)  # Check every minute
