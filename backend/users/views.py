import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer

# Get logger instances
auth_logger = logging.getLogger('users')
api_logger = logging.getLogger('api')
lms_logger = logging.getLogger('lms')


@extend_schema(
    operation_id='register_user',
    summary='Register a new user',
    description='Creates a new user account with the provided information. Returns user data and authentication token upon successful registration.',
    request=UserRegistrationSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiExample(
            'Validation Error',
            value={
                'email': ['This field is required.'],
                'password': ['This field is required.'],
                'password_confirm': ['This field is required.']
            }
        )
    },
    examples=[
        OpenApiExample(
            'Registration Request',
            value={
                'email': 'user@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'student',
                'password': 'securepassword123',
                'password_confirm': 'securepassword123'
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """
    Register a new user
    
    Creates a new user account with the provided information.
    Returns user data and authentication token upon successful registration.
    """
    auth_logger.info(f"Registration attempt from IP: {request.META.get('REMOTE_ADDR')} at {timezone.now()}")
    api_logger.info(f"POST /api/auth/register/ - Request data: {request.data}")
    
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            auth_logger.info(f"User registered successfully: {user.email} (ID: {user.id}, Role: {user.role})")
            api_logger.info(f"Registration successful for user: {user.email}")
            lms_logger.debug(f"JWT tokens created for user: {user.email}")
            
            return Response({
                'user': UserSerializer(user).data,
                'access': str(access_token),
                'refresh': str(refresh),
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            auth_logger.error(f"Registration failed for {request.data.get('email', 'unknown')}: {str(e)}")
            api_logger.error(f"Registration error: {str(e)}")
            return Response({'error': 'Registration failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        auth_logger.warning(f"Registration validation failed for {request.data.get('email', 'unknown')}: {serializer.errors}")
        api_logger.warning(f"Registration validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='login_user',
    summary='Login user',
    description='Authenticates user with email and password. Returns user data and authentication token upon successful login.',
    request=UserLoginSerializer,
    responses={
        200: OpenApiExample(
            'Login Success',
            value={
                'user': {
                    'id': 1,
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'full_name': 'John Doe',
                    'role': 'student',
                    'is_active': True,
                    'date_joined': '2025-10-12T07:48:17.849268Z'
                },
                'token': '4598dd30ddcb8a3458c6e529bf6da046d2de2836',
                'message': 'Login successful'
            }
        ),
        400: OpenApiExample(
            'Login Error',
            value={
                'non_field_errors': ['Invalid credentials']
            }
        )
    },
    examples=[
        OpenApiExample(
            'Login Request',
            value={
                'email': 'user@example.com',
                'password': 'securepassword123'
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Login user and return token
    
    Authenticates user with email and password.
    Returns user data and authentication token upon successful login.
    """
    email = request.data.get('email', 'unknown')
    auth_logger.info(f"Login attempt for email: {email} from IP: {request.META.get('REMOTE_ADDR')} at {timezone.now()}")
    api_logger.info(f"POST /api/auth/login/ - Email: {email}")
    
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            auth_logger.info(f"User logged in successfully: {user.email} (ID: {user.id}, Role: {user.role})")
            api_logger.info(f"Login successful for user: {user.email}")
            lms_logger.debug(f"JWT tokens created for user: {user.email}")
            
            return Response({
                'user': UserSerializer(user).data,
                'access': str(access_token),
                'refresh': str(refresh),
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            auth_logger.error(f"Login failed for {email}: {str(e)}")
            api_logger.error(f"Login error: {str(e)}")
            return Response({'error': 'Login failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        auth_logger.warning(f"Login failed for {email}: Invalid credentials or validation error")
        api_logger.warning(f"Login validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='logout_user',
    summary='Logout user',
    description='Logout user by deleting their authentication token.',
    responses={
        200: OpenApiExample(
            'Logout Success',
            value={
                'message': 'Logout successful'
            }
        ),
        400: OpenApiExample(
            'Logout Error',
            value={
                'message': 'Logout failed'
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout user by deleting token
    """
    user = request.user
    auth_logger.info(f"Logout attempt for user: {user.email} (ID: {user.id}) from IP: {request.META.get('REMOTE_ADDR')} at {timezone.now()}")
    api_logger.info(f"POST /api/auth/logout/ - User: {user.email}")
    
    try:
        # Get the refresh token from the request
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            auth_logger.info(f"User logged out successfully: {user.email}")
            api_logger.info(f"Logout successful for user: {user.email}")
            lms_logger.debug(f"JWT token blacklisted for user: {user.email}")
        else:
            auth_logger.warning(f"Logout without refresh token for user: {user.email}")
            api_logger.warning(f"No refresh token provided for logout: {user.email}")
        
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        auth_logger.error(f"Logout failed for {user.email}: {str(e)}")
        api_logger.error(f"Logout error: {str(e)}")
        return Response({'message': 'Logout failed'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        auth_logger.info(f"Profile access for user: {user.email} (ID: {user.id}) at {timezone.now()}")
        api_logger.info(f"GET /api/auth/profile/ - User: {user.email}")
        return user
    
    def update(self, request, *args, **kwargs):
        user = request.user
        auth_logger.info(f"Profile update attempt for user: {user.email} (ID: {user.id}) at {timezone.now()}")
        api_logger.info(f"PATCH /api/auth/profile/ - User: {user.email}, Data: {request.data}")
        
        try:
            response = super().update(request, *args, **kwargs)
            auth_logger.info(f"Profile updated successfully for user: {user.email}")
            api_logger.info(f"Profile update successful for user: {user.email}")
            return response
        except Exception as e:
            auth_logger.error(f"Profile update failed for {user.email}: {str(e)}")
            api_logger.error(f"Profile update error: {str(e)}")
            raise


@extend_schema(
    operation_id='get_dashboard',
    summary='Get user dashboard',
    description='Get user dashboard data based on their role (student, teacher, admin).',
    responses={
        200: OpenApiExample(
            'Dashboard Success',
            value={
                'user': {
                    'id': 1,
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'full_name': 'John Doe',
                    'role': 'student',
                    'is_active': True,
                    'date_joined': '2025-10-12T07:48:17.849268Z'
                },
                'role': 'student',
                'dashboard_type': 'student',
                'message': 'Welcome to Student Dashboard',
                'features': ['View Courses', 'Submit Assignments', 'Track Progress']
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_view(request):
    """
    Get user dashboard data based on role
    """
    user = request.user
    auth_logger.info(f"Dashboard access for user: {user.email} (ID: {user.id}, Role: {user.role}) from IP: {request.META.get('REMOTE_ADDR')} at {timezone.now()}")
    api_logger.info(f"GET /api/auth/dashboard/ - User: {user.email}, Role: {user.role}")
    
    try:
        dashboard_data = {
            'user': UserSerializer(user).data,
            'role': user.role,
            'dashboard_type': user.role,
        }
        
        # Add role-specific data
        if user.is_student():
            # Get student's enrolled courses
            from courses.models import Enrollment
            from courses.serializers import EnrollmentSerializer

            student_enrollments = Enrollment.objects.filter(
                student=user,
                is_active=True
            ).select_related('course')

            enrollments_serializer = EnrollmentSerializer(student_enrollments, many=True)

            dashboard_data.update({
                'message': 'Welcome to Student Dashboard',
                'features': ['View Courses', 'Submit Assignments', 'Track Progress'],
                'enrollments': enrollments_serializer.data,
                'enrollments_count': student_enrollments.count()
            })
            auth_logger.info(f"Student dashboard data provided for: {user.email} with {student_enrollments.count()} enrollments")
        elif user.is_teacher():
            # Get teacher's courses
            from courses.models import Course
            from courses.serializers import TeacherCourseSerializer

            teacher_courses = Course.objects.filter(teacher=user, is_active=True)
            courses_serializer = TeacherCourseSerializer(teacher_courses, many=True)

            dashboard_data.update({
                'message': 'Welcome to Teacher Dashboard',
                'features': ['Manage Courses', 'Grade Assignments', 'View Students'],
                'courses': courses_serializer.data,
                'courses_count': teacher_courses.count()
            })
            auth_logger.info(f"Teacher dashboard data provided for: {user.email} with {teacher_courses.count()} courses")
        elif user.is_admin():
            dashboard_data.update({
                'message': 'Welcome to Admin Dashboard',
                'features': ['Manage Users', 'System Settings', 'Analytics']
            })
            auth_logger.info(f"Admin dashboard data provided for: {user.email}")
        
        api_logger.info(f"Dashboard data successfully provided for user: {user.email}")
        lms_logger.debug(f"Dashboard access logged for user: {user.email} with role: {user.role}")
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
    except Exception as e:
        auth_logger.error(f"Dashboard access failed for {user.email}: {str(e)}")
        api_logger.error(f"Dashboard error: {str(e)}")
        return Response({'error': 'Dashboard access failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id='refresh_token',
    summary='Refresh JWT token',
    description='Refresh the access token using the refresh token.',
    request=OpenApiExample(
        'Refresh Token Request',
        value={
            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
        }
    ),
    responses={
        200: OpenApiExample(
            'Token Refresh Success',
            value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            }
        ),
        400: OpenApiExample(
            'Token Refresh Error',
            value={
                'detail': 'Token is blacklisted'
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    """
    Refresh JWT access token using refresh token
    """
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token
        
        auth_logger.info(f"Token refreshed successfully")
        api_logger.info(f"POST /api/auth/refresh/ - Token refreshed")
        
        return Response({
            'access': str(access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        auth_logger.error(f"Token refresh failed: {str(e)}")
        api_logger.error(f"Token refresh error: {str(e)}")
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)