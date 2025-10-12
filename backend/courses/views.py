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
    operation_id='list_courses',
    summary='List all courses',
    description='Get a list of all courses. Available to all authenticated users.',
    responses={
        200: CourseSerializer(many=True)
    }
)
class CourseListView(generics.ListAPIView):
    """
    List all courses - available to all authenticated users
    """
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    operation_id='create_course',
    summary='Create a new course',
    description='Create a new course. Only admins can create courses.',
    request=CourseSerializer,
    responses={
        201: CourseSerializer,
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
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
    operation_id='course_detail',
    summary='Get course details',
    description='Get detailed information about a specific course including enrollments.',
    responses={
        200: CourseDetailSerializer,
        404: OpenApiExample(
            'Not Found',
            value={'detail': 'Not found.'}
        )
    }
)
class CourseDetailView(generics.RetrieveAPIView):
    """
    Get detailed course information
    """
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    operation_id='update_course',
    summary='Update a course',
    description='Update course information. Only admins can update courses.',
    request=CourseSerializer,
    responses={
        200: CourseSerializer,
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
)
class CourseUpdateView(generics.UpdateAPIView):
    """
    Update course - only admins can update courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    operation_id='delete_course',
    summary='Delete a course',
    description='Delete a course. Only admins can delete courses.',
    responses={
        204: OpenApiExample('No Content', value={}),
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
)
class CourseDeleteView(generics.DestroyAPIView):
    """
    Delete course - only admins can delete courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    operation_id='teacher_courses',
    summary='Get teacher courses',
    description='Get all courses assigned to the current teacher.',
    responses={
        200: TeacherCourseSerializer(many=True)
    }
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
    operation_id='enroll_student',
    summary='Enroll student in course',
    description='Enroll a student in a course. Only admins can enroll students.',
    request=EnrollmentSerializer,
    responses={
        201: EnrollmentSerializer,
        400: OpenApiExample(
            'Bad Request',
            value={'detail': 'Course is full' or 'Student already enrolled'}
        ),
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
)
class EnrollmentCreateView(generics.CreateAPIView):
    """
    Enroll student in course - only admins can enroll students
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    operation_id='unenroll_student',
    summary='Unenroll student from course',
    description='Remove a student enrollment from a course. Only admins can unenroll students.',
    responses={
        204: OpenApiExample('No Content', value={}),
        403: OpenApiExample(
            'Forbidden',
            value={'detail': 'You do not have permission to perform this action.'}
        )
    }
)
class EnrollmentDeleteView(generics.DestroyAPIView):
    """
    Unenroll student from course - only admins can unenroll students
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema(
    operation_id='course_enrollments',
    summary='Get course enrollments',
    description='Get all enrollments for a specific course.',
    responses={
        200: EnrollmentSerializer(many=True)
    }
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