"""
Webhook views for external attendance session triggers
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import AttendanceSession
from .websocket_service import websocket_service
from .serializers import AttendanceSessionSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def webhook_session_started(request):
    """
    Webhook endpoint to trigger session started notifications
    Expected payload:
    {
        "session_id": 123,
        "course_id": 456,
        "action": "session_started"
    }
    """
    try:
        session_id = request.data.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the session
        session = get_object_or_404(AttendanceSession, id=session_id)
        
        # Get enrolled students
        enrolled_students = session.course.enrollments.filter(is_active=True).values_list('student_id', flat=True)
        
        # Send WebSocket notification
        websocket_service.send_session_started_notification(session, list(enrolled_students))
        
        logger.info(f'Webhook triggered session started notification for session {session_id} to {len(enrolled_students)} students')
        
        return Response({
            'message': 'Session started notification sent successfully',
            'session_id': session_id,
            'students_notified': len(enrolled_students)
        })
        
    except Exception as e:
        logger.error(f'Webhook session started error: {e}')
        return Response(
            {'error': 'Failed to send notification'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def webhook_session_ended(request):
    """
    Webhook endpoint to trigger session ended notifications
    Expected payload:
    {
        "session_id": 123,
        "action": "session_ended"
    }
    """
    try:
        session_id = request.data.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the session
        session = get_object_or_404(AttendanceSession, id=session_id)
        
        # Get enrolled students
        enrolled_students = session.course.enrollments.filter(is_active=True).values_list('student_id', flat=True)
        
        # Send WebSocket notification
        websocket_service.send_session_ended_notification(session, list(enrolled_students))
        
        logger.info(f'Webhook triggered session ended notification for session {session_id} to {len(enrolled_students)} students')
        
        return Response({
            'message': 'Session ended notification sent successfully',
            'session_id': session_id,
            'students_notified': len(enrolled_students)
        })
        
    except Exception as e:
        logger.error(f'Webhook session ended error: {e}')
        return Response(
            {'error': 'Failed to send notification'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def webhook_attendance_marked(request):
    """
    Webhook endpoint to trigger attendance marked notifications
    Expected payload:
    {
        "student_id": 123,
        "session_id": 456,
        "attendance_data": {...}
    }
    """
    try:
        student_id = request.data.get('student_id')
        session_id = request.data.get('session_id')
        attendance_data = request.data.get('attendance_data', {})
        
        if not student_id or not session_id:
            return Response(
                {'error': 'student_id and session_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send WebSocket notification
        websocket_service.send_attendance_marked_notification(student_id, attendance_data)
        
        logger.info(f'Webhook triggered attendance marked notification for student {student_id} in session {session_id}')
        
        return Response({
            'message': 'Attendance marked notification sent successfully',
            'student_id': student_id,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f'Webhook attendance marked error: {e}')
        return Response(
            {'error': 'Failed to send notification'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def webhook_broadcast_update(request):
    """
    Webhook endpoint to broadcast updates to all connected users
    Expected payload:
    {
        "update_type": "session_update",
        "data": {...}
    }
    """
    try:
        update_type = request.data.get('update_type')
        data = request.data.get('data', {})
        
        if not update_type:
            return Response(
                {'error': 'update_type is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send broadcast notification
        websocket_service.send_session_update_broadcast({
            'type': update_type,
            'data': data
        })
        
        logger.info(f'Webhook triggered broadcast update: {update_type}')
        
        return Response({
            'message': 'Broadcast update sent successfully',
            'update_type': update_type
        })
        
    except Exception as e:
        logger.error(f'Webhook broadcast update error: {e}')
        return Response(
            {'error': 'Failed to send broadcast'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
