from rest_framework import serializers
from django.utils import timezone
from .models import AttendanceSession, Attendance
from users.serializers import UserSerializer
from courses.serializers import CourseSerializer


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for attendance sessions
    """
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    teacher = UserSerializer(read_only=True)
    duration_minutes = serializers.FloatField(read_only=True)
    attendance_count = serializers.IntegerField(read_only=True)
    total_enrolled = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course', 'course_id', 'teacher', 'title', 'description',
            'classroom_latitude', 'classroom_longitude', 'classroom_name',
            'allowed_radius', 'started_at', 'ended_at', 'scheduled_duration',
            'status', 'created_at', 'updated_at', 'duration_minutes',
            'attendance_count', 'total_enrolled', 'is_active'
        ]
        read_only_fields = ['id', 'teacher', 'started_at', 'ended_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create attendance session with teacher from request"""
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)


class AttendanceSessionCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating attendance sessions
    """
    class Meta:
        model = AttendanceSession
        fields = [
            'course', 'title', 'description', 'classroom_latitude',
            'classroom_longitude', 'classroom_name', 'allowed_radius',
            'scheduled_duration'
        ]

    def create(self, validated_data):
        """Create attendance session with teacher from request"""
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for attendance records
    """
    student = UserSerializer(read_only=True)
    session = AttendanceSessionSerializer(read_only=True)
    session_id = serializers.IntegerField(write_only=True)
    is_late = serializers.BooleanField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'session', 'session_id', 'student', 'is_present', 'status',
            'student_latitude', 'student_longitude', 'location_verified',
            'distance_from_classroom', 'marked_at', 'created_at', 'updated_at',
            'is_late'
        ]
        read_only_fields = ['id', 'student', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create attendance record with student from request"""
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class AttendanceMarkSerializer(serializers.Serializer):
    """
    Serializer for marking attendance
    """
    session_id = serializers.IntegerField()
    latitude = serializers.DecimalField(max_digits=20, decimal_places=15)
    longitude = serializers.DecimalField(max_digits=20, decimal_places=15)

    def validate_session_id(self, value):
        """Validate that session exists and is active"""
        try:
            session = AttendanceSession.objects.get(id=value)
            if not session.is_active:
                raise serializers.ValidationError("Attendance session is not active")
            return value
        except AttendanceSession.DoesNotExist:
            raise serializers.ValidationError("Attendance session not found")


class AttendanceSessionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for attendance sessions with student list
    """
    course = CourseSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    attendances = AttendanceSerializer(many=True, read_only=True)
    duration_minutes = serializers.FloatField(read_only=True)
    attendance_count = serializers.IntegerField(read_only=True)
    total_enrolled = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course', 'teacher', 'title', 'description',
            'classroom_latitude', 'classroom_longitude', 'classroom_name',
            'allowed_radius', 'started_at', 'ended_at', 'scheduled_duration',
            'status', 'created_at', 'updated_at', 'duration_minutes',
            'attendance_count', 'total_enrolled', 'is_active', 'attendances'
        ]


class AttendanceSessionListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing attendance sessions
    """
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    duration_minutes = serializers.FloatField(read_only=True)
    attendance_count = serializers.IntegerField(read_only=True)
    total_enrolled = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course_code', 'course_title', 'teacher_name', 'title',
            'classroom_name', 'started_at', 'ended_at', 'status',
            'duration_minutes', 'attendance_count', 'total_enrolled', 'is_active'
        ]


class AttendanceStatsSerializer(serializers.Serializer):
    """
    Serializer for attendance statistics
    """
    total_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    total_attendance_marked = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    recent_sessions = AttendanceSessionListSerializer(many=True)
