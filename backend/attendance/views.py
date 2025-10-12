import logging
import math
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import AttendanceSession, Attendance
from .serializers import (
    AttendanceSessionSerializer, AttendanceSessionCreateSerializer,
    AttendanceSerializer, AttendanceMarkSerializer,
    AttendanceSessionDetailSerializer, AttendanceSessionListSerializer,
    AttendanceStatsSerializer
)
from courses.models import Course, Enrollment

# Get logger instances
logger = logging.getLogger('attendance')
api_logger = logging.getLogger('api')


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission for teacher-specific attendance views
    """
    def has_permission(self, request, view):
        logger.info(f"Permission check for user: {request.user.email}, authenticated: {request.user.is_authenticated}, role: {request.user.role}")
        has_permission = request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.role in ['admin', 'teacher']
        )
        logger.info(f"Permission result: {has_permission}")
        return has_permission


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in meters
    """
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


@extend_schema(
    operation_id='create_attendance_session',
    summary='Create attendance session',
    description='Create a new attendance session for a course. Only teachers can create sessions.',
    request=AttendanceSessionCreateSerializer,
    responses={
        201: AttendanceSessionSerializer,
        400: OpenApiExample(
            'Validation Error',
            value={'course_id': ['This field is required.']}
        ),
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
)
class AttendanceSessionCreateView(generics.CreateAPIView):
    """
    Create a new attendance session - only teachers can create sessions
    """
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionCreateSerializer
    permission_classes = [IsTeacherOrAdmin]

    def perform_create(self, serializer):
        """Set the teacher field and validate course access"""
        course = serializer.validated_data.get('course')
        logger.info(f"Creating session for course: {course.code} - {course.title}, user: {self.request.user.email}")
        
        # Check if teacher is assigned to this course
        if self.request.user.role == 'teacher' and course.teacher != self.request.user:
            logger.error(f"User {self.request.user.email} not assigned to course {course.code}")
            raise PermissionDenied("You are not assigned to this course")
        
        serializer.save(teacher=self.request.user)
        logger.info(f"Attendance session created by {self.request.user.email} for course {course.code}")


@extend_schema(
    operation_id='list_attendance_sessions',
    summary='List attendance sessions',
    description='Get list of attendance sessions. Teachers see their sessions, students see sessions for their courses.',
    responses={
        200: AttendanceSessionListSerializer(many=True)
    }
)
class AttendanceSessionListView(generics.ListAPIView):
    """
    List attendance sessions based on user role
    """
    serializer_class = AttendanceSessionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter sessions based on user role"""
        user = self.request.user
        
        if user.role == 'teacher':
            # Teachers see their own sessions
            return AttendanceSession.objects.filter(teacher=user).order_by('-started_at')
        elif user.role == 'student':
            # Students see sessions for their enrolled courses
            enrolled_courses = Course.objects.filter(
                enrollments__student=user,
                enrollments__is_active=True
            )
            return AttendanceSession.objects.filter(
                course__in=enrolled_courses
            ).order_by('-started_at')
        elif user.role == 'admin':
            # Admins see all sessions
            return AttendanceSession.objects.all().order_by('-started_at')
        
        return AttendanceSession.objects.none()


@extend_schema(
    operation_id='get_attendance_session',
    summary='Get attendance session details',
    description='Get detailed information about a specific attendance session.',
    responses={
        200: AttendanceSessionDetailSerializer,
        404: OpenApiExample(
            'Not Found',
            value={'detail': 'Not found.'}
        )
    }
)
class AttendanceSessionDetailView(generics.RetrieveAPIView):
    """
    Get detailed attendance session information
    """
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Check permissions for session access"""
        session = get_object_or_404(AttendanceSession, pk=self.kwargs['pk'])
        user = self.request.user
        
        # Check if user has access to this session
        if user.role == 'teacher' and session.teacher != user:
            raise PermissionDenied("You don't have access to this session")
        elif user.role == 'student':
            # Check if student is enrolled in the course
            if not Enrollment.objects.filter(
                student=user,
                course=session.course,
                is_active=True
            ).exists():
                raise PermissionDenied("You are not enrolled in this course")
        
        return session


@extend_schema(
    operation_id='end_attendance_session',
    summary='End attendance session',
    description='End an active attendance session. Only the teacher who started the session can end it.',
    responses={
        200: OpenApiExample(
            'Success',
            value={'message': 'Attendance session ended successfully'}
        ),
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
)
@api_view(['POST'])
@permission_classes([IsTeacherOrAdmin])
def end_attendance_session(request, session_id):
    """
    End an active attendance session
    """
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Check if teacher owns this session
    if request.user.role == 'teacher' and session.teacher != request.user:
        raise PermissionDenied("You can only end your own sessions")
    
    if session.status != 'active':
        return Response(
            {'error': 'Session is not active'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session.end_session()
    logger.info(f"Attendance session {session.title} ended by {request.user.email}")
    
    return Response({
        'message': 'Attendance session ended successfully',
        'session': AttendanceSessionSerializer(session).data
    })


@extend_schema(
    operation_id='get_active_sessions',
    summary='Get active attendance sessions',
    description='Get all active attendance sessions for the current user.',
    responses={
        200: AttendanceSessionListSerializer(many=True)
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_active_sessions(request):
    """
    Get active attendance sessions for the current user
    """
    user = request.user
    
    if user.role == 'student':
        # Get sessions for enrolled courses
        enrolled_courses = Course.objects.filter(
            enrollments__student=user,
            enrollments__is_active=True
        )
        sessions = AttendanceSession.objects.filter(
            course__in=enrolled_courses,
            status='active'
        ).order_by('-started_at')
    elif user.role == 'teacher':
        # Get teacher's active sessions
        sessions = AttendanceSession.objects.filter(
            teacher=user,
            status='active'
        ).order_by('-started_at')
    elif user.role == 'admin':
        # Get all active sessions
        sessions = AttendanceSession.objects.filter(
            status='active'
        ).order_by('-started_at')
    else:
        sessions = AttendanceSession.objects.none()
    
    serializer = AttendanceSessionListSerializer(sessions, many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id='mark_attendance',
    summary='Mark attendance',
    description='Mark attendance for a student in an active session with location verification.',
    request=AttendanceMarkSerializer,
    responses={
        200: OpenApiExample(
            'Success',
            value={
                'message': 'Attendance marked successfully',
                'attendance': {
                    'id': 1,
                    'is_present': True,
                    'status': 'present',
                    'location_verified': True,
                    'distance_from_classroom': 25.5
                }
            }
        ),
        400: OpenApiExample(
            'Validation Error',
            value={'error': 'Location verification failed'}
        )
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_attendance(request):
    """
    Mark attendance for a student with location verification
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Only students can mark attendance'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = AttendanceMarkSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data['session_id']
    student_lat = serializer.validated_data['latitude']
    student_lon = serializer.validated_data['longitude']
    
    # Get the session
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Check if session is active
    if not session.is_active:
        return Response(
            {'error': 'Attendance session is not active'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if student is enrolled in the course
    if not Enrollment.objects.filter(
        student=request.user,
        course=session.course,
        is_active=True
    ).exists():
        return Response(
            {'error': 'You are not enrolled in this course'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Handle special case where coordinates are 0,0 (no location permission or outside radius)
    if student_lat == 0 and student_lon == 0:
        distance = float('inf')  # Set to infinity to indicate no location
        location_verified = False
    else:
        # Calculate distance from classroom
        distance = calculate_distance(
            session.classroom_latitude,
            session.classroom_longitude,
            student_lat,
            student_lon
        )
        
        # Check if location is within allowed radius
        location_verified = distance <= session.allowed_radius
    
    # Get or create attendance record
    attendance, created = Attendance.objects.get_or_create(
        session=session,
        student=request.user,
        defaults={
            'is_present': False,
            'status': 'absent'
        }
    )
    
    if not created and attendance.is_present:
        return Response(
            {'error': 'Attendance already marked'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark attendance
    attendance.mark_attendance(
        latitude=student_lat,
        longitude=student_lon,
        location_verified=location_verified,
        distance=distance
    )
    
    # Update status based on location verification
    if location_verified:
        attendance.status = 'present'
    else:
        attendance.status = 'absent'
        attendance.is_present = False
    
    attendance.save()
    
    logger.info(f"Attendance marked by {request.user.email} for session {session.title}")
    
    # Handle infinity distance in response
    response_distance = distance if distance != float('inf') else -1
    
    return Response({
        'message': 'Attendance marked successfully',
        'attendance': AttendanceSerializer(attendance).data,
        'location_verified': location_verified,
        'distance': response_distance,
        'allowed_radius': session.allowed_radius
    })


@extend_schema(
    operation_id='get_student_notifications',
    summary='Get student notifications',
    description='Get active sessions and notifications for students.',
    responses={
        200: OpenApiExample(
            'Student Notifications',
            value={
                'active_sessions': [
                    {
                        'id': 1,
                        'title': 'Lecture 1',
                        'course_code': 'CS101',
                        'classroom_name': 'Room 101',
                        'started_at': '2025-01-12T10:00:00Z',
                        'allowed_radius': 50
                    }
                ],
                'notifications': [
                    {
                        'type': 'attendance_session_started',
                        'message': 'New attendance session started for CS101',
                        'session_id': 1
                    }
                ]
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_student_notifications(request):
    """
    Get notifications and active sessions for students
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Only students can access notifications'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get active sessions for student's enrolled courses
        from courses.models import Enrollment
        enrolled_courses = Course.objects.filter(
            enrollments__student=request.user,
            enrollments__is_active=True
        )
        
        active_sessions = AttendanceSession.objects.filter(
            course__in=enrolled_courses,
            status='active'
        ).order_by('-started_at')
        
        # Check if student has already marked attendance for these sessions
        sessions_with_attendance = []
        for session in active_sessions:
            attendance_record = Attendance.objects.filter(
                session=session,
                student=request.user
            ).first()
            
            session_data = {
                'id': session.id,
                'title': session.title,
                'course_code': session.course.code,
                'classroom_name': session.classroom_name,
                'classroom_latitude': str(session.classroom_latitude),
                'classroom_longitude': str(session.classroom_longitude),
                'started_at': session.started_at.isoformat(),
                'allowed_radius': session.allowed_radius,
                'attendance_marked': attendance_record.is_present if attendance_record else False,
                'attendance_status': attendance_record.status if attendance_record else 'not_marked'
            }
            sessions_with_attendance.append(session_data)
        
        # Generate notifications for new sessions
        notifications = []
        for session in sessions_with_attendance:
            if not session['attendance_marked']:
                notifications.append({
                    'type': 'attendance_session_started',
                    'message': f"New attendance session started for {session['course_code']}",
                    'session_id': session['id'],
                    'title': session['title']
                })
        
        return Response({
            'active_sessions': sessions_with_attendance,
            'notifications': notifications,
            'total_sessions': len(sessions_with_attendance),
            'unmarked_sessions': len([s for s in sessions_with_attendance if not s['attendance_marked']])
        })
        
    except Exception as e:
        logger.error(f"Error getting student notifications: {str(e)}")
        return Response(
            {'error': 'Failed to get notifications'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id='get_attendance_stats',
    summary='Get attendance statistics',
    description='Get attendance statistics for teachers and admins.',
    responses={
        200: AttendanceStatsSerializer
    }
)
@api_view(['GET'])
@permission_classes([IsTeacherOrAdmin])
def get_attendance_stats(request):
    """
    Get attendance statistics
    """
    user = request.user
    
    if user.role == 'teacher':
        # Get teacher's sessions
        sessions = AttendanceSession.objects.filter(teacher=user)
    else:
        # Admin sees all sessions
        sessions = AttendanceSession.objects.all()
    
    total_sessions = sessions.count()
    active_sessions = sessions.filter(status='active').count()
    total_attendance = Attendance.objects.filter(session__in=sessions, is_present=True).count()
    
    # Calculate attendance rate
    total_possible_attendance = sessions.aggregate(
        total=Count('attendances')
    )['total'] or 0
    
    attendance_rate = (total_attendance / total_possible_attendance * 100) if total_possible_attendance > 0 else 0
    
    # Get recent sessions
    recent_sessions = sessions.order_by('-started_at')[:5]
    recent_sessions_data = AttendanceSessionListSerializer(recent_sessions, many=True).data
    
    stats = {
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'total_attendance_marked': total_attendance,
        'attendance_rate': round(attendance_rate, 2),
        'recent_sessions': recent_sessions_data
    }
    
    return Response(stats)
