"""
Management command to automatically end expired attendance sessions
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendance.models import AttendanceSession
from attendance.websocket_service import websocket_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically end attendance sessions that have exceeded their scheduled duration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be ended without actually ending sessions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all active sessions
        active_sessions = AttendanceSession.objects.filter(status='active')
        
        ended_count = 0
        
        for session in active_sessions:
            # Calculate when the session should end
            scheduled_end_time = session.started_at + timedelta(minutes=session.scheduled_duration)
            
            # Check if current time is past the scheduled end time
            if timezone.now() >= scheduled_end_time:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Would end session: {session.title} (ID: {session.id}) '
                            f'- Started: {session.started_at}, Duration: {session.scheduled_duration} min'
                        )
                    )
                else:
                    # End the session
                    session.end_session()
                    
                    # Send WebSocket notification to enrolled students
                    try:
                        enrolled_students = session.course.enrollments.filter(is_active=True).values_list('student_id', flat=True)
                        websocket_service.send_session_ended_notification(session, list(enrolled_students))
                        logger.info(f'Sent session ended notification for session {session.id} to {len(enrolled_students)} students')
                    except Exception as e:
                        logger.error(f'Failed to send WebSocket notification: {e}')
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Ended session: {session.title} (ID: {session.id}) '
                            f'- Started: {session.started_at}, Duration: {session.scheduled_duration} min'
                        )
                    )
                    
                    logger.info(f'Auto-ended session {session.id} - {session.title}')
                
                ended_count += 1
        
        if ended_count == 0:
            self.stdout.write(self.style.SUCCESS('No sessions to end'))
        else:
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'[DRY RUN] Would end {ended_count} session(s)')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully ended {ended_count} session(s)')
                )
