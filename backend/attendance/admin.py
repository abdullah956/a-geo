from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceSession, Attendance, AttendanceToken


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'course', 'teacher', 'classroom_name', 
        'status', 'started_at', 'attendance_count', 'total_enrolled'
    ]
    list_filter = ['status', 'course', 'teacher', 'started_at']
    search_fields = ['title', 'course__code', 'course__title', 'teacher__email']
    readonly_fields = ['started_at', 'ended_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('course', 'teacher', 'title', 'description')
        }),
        ('Location Settings', {
            'fields': ('classroom_name', 'classroom_latitude', 'classroom_longitude', 'allowed_radius')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'scheduled_duration', 'status')
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


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'session', 'status', 'is_present', 
        'location_verified', 'marked_at', 'distance_display'
    ]
    list_filter = ['status', 'is_present', 'location_verified', 'session__course', 'marked_at']
    search_fields = ['student__email', 'student__first_name', 'student__last_name', 'session__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('session', 'student', 'is_present', 'status', 'marked_at')
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


@admin.register(AttendanceToken)
class AttendanceTokenAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'is_active', 'is_valid_display', 
        'created_at', 'expires_at', 'used_count', 'max_uses'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['session__title', 'session__course__code', 'token_hash']
    readonly_fields = ['token', 'token_hash', 'created_at', 'used_count']
    
    fieldsets = (
        ('Token Information', {
            'fields': ('session', 'token', 'token_hash')
        }),
        ('Validity', {
            'fields': ('is_active', 'created_at', 'expires_at', 'max_uses', 'used_count')
        })
    )
    
    def is_valid_display(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_display.short_description = 'Valid'
