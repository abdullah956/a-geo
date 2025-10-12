import logging
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .managers import UserManager

# Get logger instance
auth_logger = logging.getLogger('users')


class User(AbstractUser):
    """
    Custom User model with email as the primary identifier
    """
    USER_ROLES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='student')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Remove username field since we're using email
    username = None
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_student(self):
        return self.role == 'student'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def save(self, *args, **kwargs):
        """
        Override save method to log user creation and updates
        """
        is_new = self.pk is None
        
        if is_new:
            auth_logger.info(f"Creating new user: {self.email} with role: {self.role}")
        else:
            auth_logger.info(f"Updating user: {self.email} (ID: {self.pk})")
        
        super().save(*args, **kwargs)
        
        if is_new:
            auth_logger.info(f"User created successfully: {self.email} (ID: {self.pk}) at {timezone.now()}")
        else:
            auth_logger.info(f"User updated successfully: {self.email} (ID: {self.pk}) at {timezone.now()}")
    
    def delete(self, *args, **kwargs):
        """
        Override delete method to handle related objects and log user deletion
        """
        auth_logger.warning(f"Deleting user: {self.email} (ID: {self.pk}) at {timezone.now()}")
        
        try:
            # Delete related JWT tokens first (if available)
            try:
                from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
                OutstandingToken.objects.filter(user=self).delete()
            except Exception:
                pass  # JWT models might not be available
            
            # Delete user sessions
            try:
                from django.contrib.sessions.models import Session
                Session.objects.filter(session_data__contains=f'"_auth_user_id":"{self.pk}"').delete()
            except Exception:
                pass
            
            # Delete any other related objects that might cause foreign key constraints
            # This ensures clean deletion without foreign key errors
            
            super().delete(*args, **kwargs)
            auth_logger.warning(f"User deleted successfully: {self.email} (ID: {self.pk}) at {timezone.now()}")
            
        except Exception as e:
            auth_logger.error(f"Error deleting user {self.email}: {str(e)}")
            # If there are still foreign key constraints, try to delete with CASCADE
            try:
                from django.db import transaction
                with transaction.atomic():
                    # Force delete with CASCADE
                    super().delete(*args, **kwargs)
                    auth_logger.warning(f"User force deleted: {self.email} (ID: {self.pk}) at {timezone.now()}")
            except Exception as cascade_error:
                auth_logger.error(f"Failed to delete user {self.email} even with CASCADE: {str(cascade_error)}")
                raise cascade_error