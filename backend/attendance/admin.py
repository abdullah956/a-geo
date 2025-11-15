from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import AttendanceSession, Attendance, AttendanceToken


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'course', 'teacher', 'classroom_name', 
        'status', 'started_at_display', 'attendance_count', 'total_enrolled'
    ]
    list_filter = ['status', 'course', 'teacher', 'started_at']
    search_fields = ['title', 'course__code', 'course__title', 'teacher__email']
    readonly_fields = ['started_at', 'ended_at', 'created_at', 'updated_at', 'started_at_display', 'ended_at_display']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('course', 'teacher', 'title', 'description')
        }),
        ('Location Settings', {
            'fields': ('classroom_name', 'classroom_latitude', 'classroom_longitude', 'allowed_radius')
        }),
        ('Timing', {
            'fields': ('started_at_display', 'ended_at_display', 'scheduled_duration', 'status'),
            'description': 'All times are displayed in UTC timezone'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def attendance_count(self, obj):
        return obj.attendance_count
    attendance_count.short_description = 'Attendance Count'
    
    def total_enrolled(self, obj):
        return obj.total_enrolled
    total_enrolled.short_description = 'Total Enrolled'
    
    def started_at_display(self, obj):
        """Display started_at with UTC timezone indicator"""
        if obj.started_at:
            # Convert to UTC if timezone-aware
            if timezone.is_aware(obj.started_at):
                utc_time = obj.started_at.astimezone(timezone.utc)
            else:
                utc_time = obj.started_at
            return format_html(
                '<span style="font-family: monospace;">{}</span> <span style="color: #666; font-size: 0.9em;">(UTC)</span>',
                utc_time.strftime('%Y-%m-%d %H:%M:%S')
            )
        return '-'
    started_at_display.short_description = 'Started At (UTC)'
    
    def ended_at_display(self, obj):
        """Display ended_at with UTC timezone indicator"""
        if obj.ended_at:
            # Convert to UTC if timezone-aware
            if timezone.is_aware(obj.ended_at):
                utc_time = obj.ended_at.astimezone(timezone.utc)
            else:
                utc_time = obj.ended_at
            return format_html(
                '<span style="font-family: monospace;">{}</span> <span style="color: #666; font-size: 0.9em;">(UTC)</span>',
                utc_time.strftime('%Y-%m-%d %H:%M:%S')
            )
        return '-'
    ended_at_display.short_description = 'Ended At (UTC)'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'session', 'status', 'is_present', 
        'location_verified', 'marked_at_display', 'distance_display'
    ]
    list_filter = ['status', 'is_present', 'location_verified', 'session__course', 'marked_at']
    search_fields = ['student__email', 'student__first_name', 'student__last_name', 'session__title']
    readonly_fields = ['created_at', 'updated_at', 'marked_at_display']
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('session', 'student', 'is_present', 'status', 'marked_at_display'),
            'description': 'All times are displayed in UTC timezone'
        }),
        ('Location Verification', {
            'fields': ('student_latitude', 'student_longitude', 'location_verified', 'distance_from_classroom')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def distance_display(self, obj):
        if obj.distance_from_classroom is not None:
            return f"{obj.distance_from_classroom:.1f}m"
        return "N/A"
    distance_display.short_description = 'Distance from Classroom'
    
    def marked_at_display(self, obj):
        """Display marked_at with UTC timezone indicator"""
        if obj.marked_at:
            # Convert to UTC if timezone-aware
            if timezone.is_aware(obj.marked_at):
                utc_time = obj.marked_at.astimezone(timezone.utc)
            else:
                utc_time = obj.marked_at
            return format_html(
                '<span style="font-family: monospace;">{}</span> <span style="color: #666; font-size: 0.9em;">(UTC)</span>',
                utc_time.strftime('%Y-%m-%d %H:%M:%S')
            )
        return '-'
    marked_at_display.short_description = 'Marked At (UTC)'


@admin.register(AttendanceToken)
class AttendanceTokenAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'is_active', 'is_valid_display', 
        'created_at_display', 'expires_at_display', 'used_count', 'max_uses'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['session__title', 'session__course__code', 'token_hash']
    readonly_fields = ['token', 'token_hash', 'created_at', 'used_count', 'created_at_display', 'expires_at_display']
    
    fieldsets = (
        ('Token Information', {
            'fields': ('session', 'token', 'token_hash')
        }),
        ('Validity', {
            'fields': ('is_active', 'created_at_display', 'expires_at_display', 'max_uses', 'used_count'),
            'description': 'All times are displayed in UTC timezone'
        })
    )
    
    def is_valid_display(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_display.short_description = 'Valid'
    
    def created_at_display(self, obj):
        """Display created_at with UTC timezone indicator"""
        if obj.created_at:
            # Convert to UTC if timezone-aware
            if timezone.is_aware(obj.created_at):
                utc_time = obj.created_at.astimezone(timezone.utc)
            else:
                utc_time = obj.created_at
            return format_html(
                '<span style="font-family: monospace;">{}</span> <span style="color: #666; font-size: 0.9em;">(UTC)</span>',
                utc_time.strftime('%Y-%m-%d %H:%M:%S')
            )
        return '-'
    created_at_display.short_description = 'Created At (UTC)'
    
    def expires_at_display(self, obj):
        """Display expires_at with UTC timezone indicator"""
        if obj.expires_at:
            # Convert to UTC if timezone-aware
            if timezone.is_aware(obj.expires_at):
                utc_time = obj.expires_at.astimezone(timezone.utc)
            else:
                utc_time = obj.expires_at
            return format_html(
                '<span style="font-family: monospace;">{}</span> <span style="color: #666; font-size: 0.9em;">(UTC)</span>',
                utc_time.strftime('%Y-%m-%d %H:%M:%S')
            )
        return '-'
    expires_at_display.short_description = 'Expires At (UTC)'
