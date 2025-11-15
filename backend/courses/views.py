import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Course, Enrollment
from .serializers import (
    CourseSerializer, CourseDetailSerializer, EnrollmentSerializer,
    TeacherCourseSerializer, UserSerializer
)

# Get logger instances
logger = logging.getLogger('courses')
api_logger = logging.getLogger('api')

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to create/modify courses
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_superuser or request.user.role == 'admin')


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission for teacher-specific views
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.role in ['admin', 'teacher']
        )


@extend_schema(
    summary='List all courses',
    description='Get a list of all courses. Available to all authenticated users.',
    responses={200: CourseSerializer(many=True)}
)
class CourseListView(generics.ListAPIView):
    """
    List all courses - available to all authenticated users
    """
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary='Create a new course',
    description='Create a new course. Only admins can create courses.',
    request=CourseSerializer,
    responses={201: CourseSerializer}
)
class CourseCreateView(generics.CreateAPIView):
    """
    Create a new course - only admins can create courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        """Set the created_by field"""
        serializer.save(created_by=self.request.user)


@extend_schema(
    summary='Get course details',
    description='Get detailed information about a specific course including enrollments.',
    responses={200: CourseDetailSerializer}
)
class CourseDetailView(generics.RetrieveAPIView):
    """
    Get detailed course information
    """
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary='Update a course',
    description='Update course information. Only admins can update courses.',
    request=CourseSerializer,
    responses={200: CourseSerializer}
)
class CourseUpdateView(generics.UpdateAPIView):
    """
    Update course - only admins can update courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    summary='Delete a course',
    description='Delete a course. Only admins can delete courses.',
    responses={204: None}
)
class CourseDeleteView(generics.DestroyAPIView):
    """
    Delete course - only admins can delete courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    summary='Get teacher courses',
    description='Get all courses assigned to the current teacher.',
    responses={200: TeacherCourseSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsTeacherOrAdmin])
def teacher_courses_view(request):
    """
    Get courses for the current teacher
    """
    user = request.user
    logger.info(f"Teacher courses access for: {user.email} (Role: {user.role})")

    if user.role == 'teacher':
        courses = Course.objects.filter(teacher=user, is_active=True)
    else:  # Admin
        courses = Course.objects.filter(is_active=True)

    serializer = TeacherCourseSerializer(courses, many=True)
    return Response(serializer.data)


@extend_schema(
    summary='Enroll student in course',
    description='Enroll a student in a course. Only admins can enroll students.',
    request=EnrollmentSerializer,
    responses={201: EnrollmentSerializer}
)
class EnrollmentCreateView(generics.CreateAPIView):
    """
    Enroll student in course - only admins can enroll students
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    summary='Unenroll student from course',
    description='Remove a student enrollment from a course. Only admins can unenroll students.',
    responses={204: None}
)
class EnrollmentDeleteView(generics.DestroyAPIView):
    """
    Unenroll student from course - only admins can unenroll students
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    summary='Get course enrollments',
    description='Get all enrollments for a specific course.',
    responses={200: EnrollmentSerializer(many=True)}
)
class CourseEnrollmentsView(generics.ListAPIView):
    """
    Get all enrollments for a course
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Enrollment.objects.filter(course_id=course_id, is_active=True)


@extend_schema(
    summary='Get teacher students',
    description='Get all students enrolled in courses taught by the current teacher.',
    responses={200: EnrollmentSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsTeacherOrAdmin])
def teacher_students_view(request):
    """
    Get all students enrolled in courses taught by the current teacher
    """
    import logging
    logger = logging.getLogger('api')
    
    try:
        from attendance.models import AttendanceSession, Attendance
        
        logger.info(f"Teacher {request.user.email} requesting students list")
        
        # Get all courses taught by the current teacher
        teacher_courses = Course.objects.filter(teacher=request.user, is_active=True)
        logger.info(f"Found {teacher_courses.count()} courses for teacher")
        
        # Get all enrollments for these courses
        enrollments = Enrollment.objects.filter(
            course__in=teacher_courses,
            is_active=True
        ).select_related('student', 'course').order_by('course__code', 'student__last_name', 'student__first_name')
        
        logger.info(f"Found {enrollments.count()} enrollments")
        
        # Calculate attendance rates for each enrollment directly in the view
        enrollment_data = []
        for enrollment in enrollments:
            # Get ALL ended sessions for this course (case-insensitive)
            all_sessions = AttendanceSession.objects.filter(
                course=enrollment.course
            ).filter(status__iexact='ended')
            
            total_sessions = all_sessions.count()
            logger.info(f"Course {enrollment.course.code} (ID: {enrollment.course.id}): {total_sessions} ended sessions")
            
            # Debug: Check all session statuses for this course
            all_statuses = AttendanceSession.objects.filter(
                course=enrollment.course
            ).values_list('status', flat=True).distinct()
            logger.info(f"Course {enrollment.course.code}: All session statuses found: {list(all_statuses)}")
            
            attendance_data = None
            if total_sessions > 0:
                # Count ALL times student marked present in this course
                total_presents = Attendance.objects.filter(
                    session__course=enrollment.course,
                    student=enrollment.student,
                    is_present=True
                ).count()
                
                logger.info(f"Student {enrollment.student.email} in {enrollment.course.code}: {total_presents} presents out of {total_sessions} sessions")
                
                # Calculate percentage as whole number
                attendance_percentage = int(round((total_presents / total_sessions * 100), 0))
                
                # Return as dict with fraction and percentage
                attendance_data = {
                    'attended': total_presents,
                    'total': total_sessions,
                    'percentage': attendance_percentage,
                    'display': f"{total_presents}/{total_sessions} ({attendance_percentage}%)"
                }
                logger.info(f"Calculated attendance: {attendance_data['display']}")
            else:
                logger.info(f"Course {enrollment.course.code}: No ended sessions, attendance_rate will be None")
            
            # Serialize enrollment (but override attendance_rate from view calculation)
            serializer = EnrollmentSerializer(enrollment)
            enrollment_dict = serializer.data
            # Override with our calculated value
            enrollment_dict['attendance_rate'] = attendance_data
            enrollment_data.append(enrollment_dict)
        
        logger.info(f"Returning {len(enrollment_data)} students with attendance data")
        
        return Response({
            'students': enrollment_data,
            'total_students': enrollments.count(),
            'courses_count': teacher_courses.count()
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger('courses')
        logger.error(f"Error in teacher_students_view: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to fetch students: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )