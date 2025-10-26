"""
WebSocket service for sending real-time attendance notifications
"""
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import AttendanceSession
from .serializers import AttendanceSessionSerializer

logger = logging.getLogger(__name__)


class AttendanceWebSocketService:
    """
    Service for sending real-time attendance notifications via WebSocket
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_session_started_notification(self, session, enrolled_students=None):
        """
        Send notification when an attendance session starts
        
        Args:
            session (AttendanceSession): The attendance session that started
            enrolled_students (list): List of student IDs enrolled in the course
        """
        try:
            # Serialize session data
            session_data = AttendanceSessionSerializer(session).data
            
            # If no enrolled students provided, get them from the session's course
            if enrolled_students is None:
                enrolled_students = session.course.enrollments.values_list('student_id', flat=True)
            
            # Send notification to each enrolled student
            for student_id in enrolled_students:
                self._send_to_user_group(
                    user_id=student_id,
                    event_type='attendance_session_started',
                    data={'session': session_data}
                )
            
            logger.info(f'Sent session started notifications for session {session.id} to {len(enrolled_students)} students')
            
        except Exception as e:
            logger.error(f'Error sending session started notification: {e}')
    
    def send_session_ended_notification(self, session, enrolled_students=None):
        """
        Send notification when an attendance session ends
        
        Args:
            session (AttendanceSession): The attendance session that ended
            enrolled_students (list): List of student IDs enrolled in the course
        """
        try:
            # Serialize session data
            session_data = AttendanceSessionSerializer(session).data
            
            # If no enrolled students provided, get them from the session's course
            if enrolled_students is None:
                enrolled_students = session.course.enrollments.values_list('student_id', flat=True)
            
            # Send notification to each enrolled student
            for student_id in enrolled_students:
                self._send_to_user_group(
                    user_id=student_id,
                    event_type='attendance_session_ended',
                    data={'session': session_data}
                )
            
            logger.info(f'Sent session ended notifications for session {session.id} to {len(enrolled_students)} students')
            
        except Exception as e:
            logger.error(f'Error sending session ended notification: {e}')
    
    def send_attendance_marked_notification(self, student_id, attendance_data):
        """
        Send notification when a student's attendance is marked
        
        Args:
            student_id (int): ID of the student whose attendance was marked
            attendance_data (dict): Data about the attendance marking
        """
        try:
            self._send_to_user_group(
                user_id=student_id,
                event_type='attendance_marked',
                data={'attendance': attendance_data}
            )
            
            logger.info(f'Sent attendance marked notification to student {student_id}')
            
        except Exception as e:
            logger.error(f'Error sending attendance marked notification: {e}')
    
    def send_session_update_broadcast(self, update_data):
        """
        Broadcast session update to all connected users
        
        Args:
            update_data (dict): Data about the session update
        """
        try:
            self._send_to_broadcast_group(
                event_type='broadcast_session_update',
                data={'update_data': update_data}
            )
            
            logger.info('Broadcasted session update to all users')
            
        except Exception as e:
            logger.error(f'Error broadcasting session update: {e}')
    
    def _send_to_user_group(self, user_id, event_type, data):
        """Send message to a specific user's group"""
        if not self.channel_layer:
            logger.warning('Channel layer not available')
            return
        
        group_name = f'attendance_notifications_{user_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': event_type,
                'session_data': data.get('session', {}),
                'attendance_data': data.get('attendance', {}),
                **data
            }
        )
    
    def _send_to_broadcast_group(self, event_type, data):
        """Send message to broadcast group"""
        if not self.channel_layer:
            logger.warning('Channel layer not available')
            return
        
        async_to_sync(self.channel_layer.group_send)(
            'attendance_broadcast',
            {
                'type': event_type,
                'update_data': data.get('update_data', {}),
                **data
            }
        )


# Global instance
websocket_service = AttendanceWebSocketService()
