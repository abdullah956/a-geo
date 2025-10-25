from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import random
import string
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Custom User model with role-based authentication
    """
    objects = UserManager()
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_admin(self):
        return self.role == 'admin'

    def save(self, *args, **kwargs):
        # Set username to email if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class PasswordResetOTP(models.Model):
    """
    Model to store OTP for password reset
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_otps'
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_code}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            # Generate 6-digit OTP
            self.otp_code = ''.join(random.choices(string.digits, k=6))
            # Set expiry to 10 minutes from now
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if OTP is valid and not expired"""
        return not self.is_used and timezone.now() <= self.expires_at

    def send_otp_email(self):
        """Send OTP via email"""
        try:
            subject = 'Password Reset OTP - AALA LMS'
            message = f"""
            Hello {self.user.get_full_name()},
            
            You requested a password reset for your AALA LMS account.
            
            Your OTP code is: {self.otp_code}
            
            This code will expire in 10 minutes.
            
            If you didn't request this password reset, please ignore this email.
            
            Best regards,
            AALA LMS Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent to {self.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email to {self.user.email}: {str(e)}")
            return False

    @classmethod
    def create_otp_for_user(cls, user):
        """Create a new OTP for user and invalidate old ones"""
        # Invalidate all existing OTPs for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new OTP
        otp = cls.objects.create(user=user)
        return otp