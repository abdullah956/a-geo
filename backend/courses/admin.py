from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.utils.html import format_html
from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Course admin - only admins can manage courses
    """
    list_display = ('code', 'title', 'teacher', 'enrolled_students_count', 'max_students', 'is_active', 'created_at')
    list_filter = ('is_active', 'teacher', 'created_at')
    search_fields = ('code', 'title', 'teacher__email', 'teacher__first_name')
    ordering = ('-created_at',)
    actions = ['activate_courses', 'deactivate_courses']

    fieldsets = (
        ('Course Information', {
            'fields': ('code', 'title', 'description')
        }),
        ('Teacher Assignment', {
            'fields': ('teacher',),
            'description': 'Only teachers can be assigned to courses'
        }),
        ('Enrollment Settings', {
            'fields': ('max_students', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_by', 'created_at', 'updated_at', 'enrolled_students_count')

    def get_queryset(self, request):
        """Only show courses to admins"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'admin':
            return qs
        return qs.none()  # Non-admins can't see courses

    def has_add_permission(self, request):
        """Only admins can add courses"""
        return request.user.is_superuser or request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        """Only admins can change courses"""
        return request.user.is_superuser or request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        """Only admins can delete courses"""
        return request.user.is_superuser or request.user.role == 'admin'

    def save_model(self, request, obj, form, change):
        """Set created_by field when saving"""
        if not change:  # Only for new courses
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def enrolled_students_count(self, obj):
        """Display enrolled students count"""
        count = obj.enrolled_students_count
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            'red' if count >= obj.max_students else 'green',
            count,
            obj.max_students
        )
    enrolled_students_count.short_description = 'Enrolled/Max'

    def activate_courses(self, request, queryset):
        """Admin action to activate courses"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {updated} course(s).',
            messages.SUCCESS
        )
    activate_courses.short_description = "Activate selected courses"

    def deactivate_courses(self, request, queryset):
        """Admin action to deactivate courses"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} course(s).',
            messages.SUCCESS
        )
    deactivate_courses.short_description = "Deactivate selected courses"


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """
    Enrollment admin - admins can manage student enrollments
    """
    list_display = ('student', 'course', 'enrolled_at', 'is_active', 'grade')
    list_filter = ('is_active', 'course', 'enrolled_at')
    search_fields = ('student__email', 'course__code', 'course__title')
    ordering = ('-enrolled_at',)

    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course', 'enrolled_at')
        }),
        ('Status', {
            'fields': ('is_active', 'grade')
        }),
    )

    readonly_fields = ('enrolled_at',)

    def get_queryset(self, request):
        """Only show enrollments to admins"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'admin':
            return qs
        return qs.none()  # Non-admins can't see enrollments

    def has_add_permission(self, request):
        """Only admins can add enrollments"""
        return request.user.is_superuser or request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        """Only admins can change enrollments"""
        return request.user.is_superuser or request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        """Only admins can delete enrollments"""
        return request.user.is_superuser or request.user.role == 'admin'