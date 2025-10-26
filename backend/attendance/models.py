import logging
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from courses.models import Course

# Get logger instance
logger = logging.getLogger('attendance')


class AttendanceSession(models.Model):
    """
    Attendance session started by a teacher for a specific course
    """
    SESSION_STATUS = [
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        help_text="Course for this attendance session"
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='attendance_sessions',
        help_text="Teacher who started this session"
    )

    # Session details
    title = models.CharField(max_length=200, help_text="Session title (e.g., 'Lecture 1', 'Lab Session')")
    description = models.TextField(blank=True, help_text="Optional session description")

    # Location settings
    classroom_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        help_text="Classroom latitude coordinate"
    )
    classroom_longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        help_text="Classroom longitude coordinate"
    )
    classroom_name = models.CharField(
        max_length=100,
        help_text="Name of the classroom/location"
    )
    allowed_radius = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        help_text="Allowed radius in meters for attendance marking"
    )

    # Session timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    scheduled_duration = models.PositiveIntegerField(
        default=60,
        help_text="Scheduled duration in minutes"
    )

    # Session status
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS,
        default='active'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_sessions'
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save to log session creation/updates"""
        is_new = self.pk is None

        if is_new:
            logger.info(f"Creating attendance session: {self.title} for course {self.course.code}")
        else:
            logger.info(f"Updating attendance session: {self.title} (ID: {self.pk})")

        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Attendance session created: {self.title} (ID: {self.pk}) at {timezone.now()}")
        else:
            logger.info(f"Attendance session updated: {self.title} (ID: {self.pk}) at {timezone.now()}")

    def end_session(self):
        """End the attendance session and mark unmarked students as absent"""
        if self.status == 'active':
            self.status = 'ended'
            self.ended_at = timezone.now()
            self.save()
            
            # Mark all unmarked students as absent
            self.mark_unmarked_students_as_absent()
            
            logger.info(f"Attendance session ended: {self.title} (ID: {self.pk}) at {timezone.now()}")
    
    def mark_unmarked_students_as_absent(self):
        """Mark all students who didn't mark attendance as absent"""
        from courses.models import Enrollment
        
        # Get all enrolled students for this session's course
        enrolled_students = Enrollment.objects.filter(
            course=self.course,
            is_active=True
        ).select_related('student')
        
        for enrollment in enrolled_students:
            student = enrollment.student
            
            # Check if student already has an attendance record
            attendance, created = Attendance.objects.get_or_create(
                session=self,
                student=student,
                defaults={
                    'is_present': False,
                    'status': 'absent',
                    'marked_at': None
                }
            )
            
            # If attendance record was just created or student didn't mark attendance
            if created or not attendance.is_present:
                attendance.is_present = False
                attendance.status = 'absent'
                attendance.save()
                logger.info(f"Marked {student.email} as absent for session {self.title}")

    @property
    def is_active(self):
        """Check if session is currently active"""
        return self.status == 'active'

    @property
    def duration_minutes(self):
        """Get session duration in minutes"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() / 60
        return (timezone.now() - self.started_at).total_seconds() / 60

    @property
    def enrolled_students(self):
        """Get all enrolled students for this course"""
        return self.course.enrollments.filter(is_active=True).select_related('student')

    @property
    def attendance_count(self):
        """Get count of students who marked attendance"""
        return self.attendances.filter(is_present=True).count()

    @property
    def total_enrolled(self):
        """Get total enrolled students"""
        return self.enrolled_students.count()


class Attendance(models.Model):
    """
    Individual student attendance record
    """
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Attendance session"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendances',
        help_text="Student who marked attendance"
    )

    # Attendance details
    is_present = models.BooleanField(default=False, help_text="Whether student is present")
    status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS,
        default='absent',
        help_text="Attendance status"
    )

    # Location verification
    student_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Student's latitude when marking attendance"
    )
    student_longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Student's longitude when marking attendance"
    )
    location_verified = models.BooleanField(
        default=False,
        help_text="Whether location was verified within allowed radius"
    )
    distance_from_classroom = models.FloatField(
        null=True,
        blank=True,
        help_text="Distance from classroom in meters"
    )

    # Timing
    marked_at = models.DateTimeField(null=True, blank=True, help_text="When student marked attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendances'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        unique_together = ['session', 'student']  # One attendance record per student per session
        ordering = ['-marked_at']

    def __str__(self):
        return f"{self.student.email} - {self.session.title} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save to log attendance marking"""
        is_new = self.pk is None

        if is_new:
            logger.info(f"Creating attendance record for {self.student.email} in session {self.session.title}")
        else:
            logger.info(f"Updating attendance record for {self.student.email} in session {self.session.title}")

        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Attendance record created: {self.student.email} -> {self.session.title} at {timezone.now()}")
        else:
            logger.info(f"Attendance record updated: {self.student.email} -> {self.session.title} at {timezone.now()}")

    def mark_attendance(self, latitude=None, longitude=None, location_verified=False, distance=None):
        """Mark student as present with location verification"""
        self.is_present = True
        self.status = 'present'
        self.marked_at = timezone.now()
        
        if latitude and longitude:
            self.student_latitude = latitude
            self.student_longitude = longitude
            self.location_verified = location_verified
            self.distance_from_classroom = distance
        
        self.save()
        logger.info(f"Attendance marked for {self.student.email} in session {self.session.title}")

    @property
    def is_late(self):
        """Check if student was late (marked attendance after session started + 15 minutes)"""
        if not self.marked_at:
            return False
        
        late_threshold = self.session.started_at + timezone.timedelta(minutes=15)
        return self.marked_at > late_threshold


class AttendanceToken(models.Model):
    """
    QR code token for attendance marking
    """
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='tokens',
        help_text="Attendance session this token belongs to"
    )
    token = models.CharField(
        max_length=500,
        unique=True,
        help_text="JWT token for attendance verification"
    )
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="SHA-256 hash of the token for quick lookup"
    )
    
    # Token validity
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Token expiration time")
    is_active = models.BooleanField(default=True, help_text="Whether token is still valid")
    
    # Usage tracking
    used_count = models.PositiveIntegerField(default=0, help_text="Number of times token was used")
    max_uses = models.PositiveIntegerField(default=0, help_text="Maximum allowed uses (0 = unlimited)")
    
    class Meta:
        db_table = 'attendance_tokens'
        verbose_name = 'Attendance Token'
        verbose_name_plural = 'Attendance Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['session', 'is_active']),
        ]
    
    def __str__(self):
        return f"Token for {self.session.title} (expires: {self.expires_at})"
    
    @property
    def is_expired(self):
        """Check if token has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (active, not expired, under max uses)"""
        if not self.is_active or self.is_expired:
            return False
        
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        
        return True
    
    def mark_used(self):
        """Mark token as used"""
        self.used_count += 1
        self.save(update_fields=['used_count'])
        logger.info(f"Token {self.id} used ({self.used_count} times)")
    
    def deactivate(self):
        """Deactivate token"""
        self.is_active = False
        self.save(update_fields=['is_active'])
        logger.info(f"Token {self.id} deactivated")
