from rest_framework import serializers
from .models import Course, Enrollment
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id', 'email')


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model
    """
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    enrolled_students_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'classroom', 'teacher', 'teacher_name',
            'max_students', 'is_active', 'enrolled_students_count', 'is_full',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'enrolled_students_count', 'is_full')

    def validate_teacher(self, value):
        """Validate that only teachers can be assigned to courses"""
        if value and value.role != 'teacher':
            raise serializers.ValidationError("Only teachers can be assigned to courses.")
        return value

    def create(self, validated_data):
        """Set created_by field during creation"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Enrollment model
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    grade_display = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'student_email', 'course', 'course_title', 'course_code',
            'enrolled_at', 'is_active', 'grade', 'grade_display', 'attendance_rate'
        ]
        read_only_fields = ('id', 'enrolled_at')

    def get_grade_display(self, obj):
        """Format grade as percentage (e.g., 80/100%)"""
        if obj.grade is not None:
            return f"{obj.grade}/100%"
        return None
    
    def get_attendance_rate(self, obj):
        """Calculate attendance rate for this student in this course"""
        from attendance.models import AttendanceSession, Attendance
        from django.db.models import Count, Q
        import logging
        
        try:
            # Get all attendance sessions for this course (ended sessions only)
            # Use case-insensitive filter to be safe
            sessions = AttendanceSession.objects.filter(
                course=obj.course
            ).filter(
                status__iexact='ended'
            )
            
            total_sessions = sessions.count()
            
            # Debug logging
            logger = logging.getLogger('courses')
            logger.debug(f"Course {obj.course.code}: Found {total_sessions} ended sessions")
            
            if total_sessions == 0:
                # Check if there are any sessions at all
                all_sessions = AttendanceSession.objects.filter(course=obj.course).count()
                logger.debug(f"Course {obj.course.code}: Total sessions (all statuses): {all_sessions}")
                return None  # No ended sessions yet
            
            # Get all attendance records for this student in these sessions
            # When a session ends, all students should have attendance records (present or absent)
            all_attendances = Attendance.objects.filter(
                session__in=sessions,
                student=obj.student
            )
            
            total_records = all_attendances.count()
            logger.debug(f"Student {obj.student.email} in {obj.course.code}: {total_records} attendance records for {total_sessions} sessions")
            
            # Count how many sessions the student actually attended (is_present=True)
            attended_count = all_attendances.filter(is_present=True).count()
            logger.debug(f"Student {obj.student.email} in {obj.course.code}: Attended {attended_count} out of {total_sessions}")
            
            # Calculate rate: attended / total ended sessions
            attendance_rate = (attended_count / total_sessions * 100) if total_sessions > 0 else 0.0
            
            result = round(attendance_rate, 2)
            logger.debug(f"Student {obj.student.email} in {obj.course.code}: Attendance rate = {result}%")
            
            return result
        except Exception as e:
            # Log error but return None to avoid breaking the serializer
            logger = logging.getLogger('courses')
            logger.error(f"Error calculating attendance rate for student {obj.student.id} in course {obj.course.id}: {e}", exc_info=True)
        return None

    def validate(self, data):
        """Validate enrollment constraints"""
        student = data['student']
        course = data['course']

        # Check if student is already enrolled
        if Enrollment.objects.filter(student=student, course=course, is_active=True).exists():
            raise serializers.ValidationError("Student is already enrolled in this course.")

        # Check if course is full
        if course.is_full:
            raise serializers.ValidationError("Course is full. Cannot enroll more students.")

        return data


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Detailed course serializer with enrollment information
    """
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    enrolled_students_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    enrollments = EnrollmentSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'classroom', 'teacher', 'teacher_name',
            'max_students', 'is_active', 'enrolled_students_count', 'is_full',
            'enrollments', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'enrolled_students_count', 'is_full')


class TeacherCourseSerializer(serializers.ModelSerializer):
    """
    Serializer for courses taught by a specific teacher
    """
    enrolled_students_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'classroom', 'max_students',
            'enrolled_students_count', 'is_full', 'created_at'
        ]
        read_only_fields = ('id', 'created_at', 'enrolled_students_count', 'is_full')
