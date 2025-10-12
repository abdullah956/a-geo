import logging
from django.db import models
from django.utils import timezone
from users.models import User

# Get logger instance
logger = logging.getLogger('courses')

class Course(models.Model):
    """
    Course model - only admins can create and assign teachers
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True, help_text="Unique course code (e.g., CS101)")

    # Teacher assigned to this course
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        help_text="Teacher assigned to this course"
    )

    # Course details
    max_students = models.PositiveIntegerField(default=50, help_text="Maximum number of students")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_courses',
        help_text="Admin who created this course"
    )

    class Meta:
        db_table = 'courses'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code}: {self.title}"

    def save(self, *args, **kwargs):
        """Override save to log course creation/updates"""
        is_new = self.pk is None

        if is_new:
            logger.info(f"Creating new course: {self.code} - {self.title}")
        else:
            logger.info(f"Updating course: {self.code} - {self.title}")

        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Course created successfully: {self.code} (ID: {self.pk}) at {timezone.now()}")
        else:
            logger.info(f"Course updated successfully: {self.code} (ID: {self.pk}) at {timezone.now()}")

    def delete(self, *args, **kwargs):
        """Override delete to log course deletion"""
        logger.warning(f"Deleting course: {self.code} - {self.title} (ID: {self.pk}) at {timezone.now()}")
        super().delete(*args, **kwargs)
        logger.warning(f"Course deleted: {self.code} (ID: {self.pk}) at {timezone.now()}")

    @property
    def enrolled_students_count(self):
        """Get count of enrolled students"""
        return self.enrollments.filter(is_active=True).count()

    @property
    def is_full(self):
        """Check if course is full"""
        return self.enrolled_students_count >= self.max_students


class Enrollment(models.Model):
    """
    Student enrollment in courses
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Grade information
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final grade (0.00-100.00)"
    )

    class Meta:
        db_table = 'enrollments'
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['student', 'course']  # Prevent duplicate enrollments

    def __str__(self):
        return f"{self.student.email} -> {self.course.code}"

    def save(self, *args, **kwargs):
        """Override save to log enrollment"""
        is_new = self.pk is None

        if is_new:
            logger.info(f"Student {self.student.email} enrolling in course {self.course.code}")
        else:
            logger.info(f"Updating enrollment: {self.student.email} in {self.course.code}")

        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Enrollment created: {self.student.email} -> {self.course.code} at {timezone.now()}")