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
            'id', 'code', 'title', 'description', 'teacher', 'teacher_name',
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
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    grade_display = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'course_title', 'course_code',
            'enrolled_at', 'is_active', 'grade', 'grade_display'
        ]
        read_only_fields = ('id', 'enrolled_at')

    def get_grade_display(self, obj):
        """Format grade as percentage (e.g., 80/100%)"""
        if obj.grade is not None:
            return f"{obj.grade}/100%"
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
            'id', 'code', 'title', 'description', 'teacher', 'teacher_name',
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
            'id', 'code', 'title', 'description', 'max_students',
            'enrolled_students_count', 'is_full', 'created_at'
        ]
        read_only_fields = ('id', 'created_at', 'enrolled_students_count', 'is_full')
