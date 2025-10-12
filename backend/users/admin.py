from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.db import transaction
from django.utils.html import format_html
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with safe deletion
    """
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined', 'delete_button')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['delete_selected_users']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def delete_button(self, obj):
        """Add a delete button for each user"""
        if obj.pk:
            return format_html(
                '<a class="button" href="javascript:void(0)" onclick="deleteUser({})">Delete</a>',
                obj.pk
            )
        return '-'
    delete_button.short_description = 'Actions'
    
    def delete_selected_users(self, request, queryset):
        """Custom action to safely delete selected users"""
        deleted_count = 0
        failed_deletions = []
        
        for user in queryset:
            try:
                # Use raw SQL to delete all related data first
                from django.db import connection
                with connection.cursor() as cursor:
                    # Delete from all related tables
                    cursor.execute("DELETE FROM django_session WHERE session_data LIKE %s", [f'%"_auth_user_id":"{user.pk}"%'])
                    cursor.execute("DELETE FROM users_groups WHERE user_id = %s", [user.pk])
                    cursor.execute("DELETE FROM users_user_permissions WHERE user_id = %s", [user.pk])
                    cursor.execute("DELETE FROM authtoken_token WHERE user_id = %s", [user.pk])
                    cursor.execute("DELETE FROM django_admin_log WHERE user_id = %s", [user.pk])
                    
                    # Try to delete JWT tokens if tables exist
                    try:
                        cursor.execute("DELETE FROM token_blacklist_blacklistedtoken WHERE token_id IN (SELECT id FROM token_blacklist_outstandingtoken WHERE user_id = %s)", [user.pk])
                        cursor.execute("DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s", [user.pk])
                    except:
                        pass
                
                # Now delete the user
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE id = %s", [user.pk])
                    deleted_count += 1
                    
            except Exception as e:
                failed_deletions.append(f"{user.email}: {str(e)}")
        
        if deleted_count > 0:
            self.message_user(
                request,
                f'Successfully deleted {deleted_count} user(s).',
                messages.SUCCESS
            )
        
        if failed_deletions:
            self.message_user(
                request,
                f'Failed to delete: {", ".join(failed_deletions)}',
                messages.ERROR
            )
    
    delete_selected_users.short_description = "Delete selected users safely"
    
    def _cleanup_user_data(self, user):
        """Clean up related data before user deletion"""
        try:
            # Delete JWT tokens if they exist
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            OutstandingToken.objects.filter(user=user).delete()
            BlacklistedToken.objects.filter(token__user=user).delete()
        except Exception as e:
            # JWT models might not be available or migrated yet
            pass
        
        try:
            # Delete user sessions
            from django.contrib.sessions.models import Session
            Session.objects.filter(session_data__contains=f'"_auth_user_id":"{user.pk}"').delete()
        except Exception as e:
            pass
        
        try:
            # Delete any other related objects
            # Add more cleanup as needed
            pass
        except Exception as e:
            pass
    
    def delete_model(self, request, obj):
        """Override delete_model to handle cleanup"""
        try:
            # Use raw SQL to delete all related data first
            from django.db import connection
            with connection.cursor() as cursor:
                # Delete from all related tables
                cursor.execute("DELETE FROM django_session WHERE session_data LIKE %s", [f'%"_auth_user_id":"{obj.pk}"%'])
                cursor.execute("DELETE FROM users_groups WHERE user_id = %s", [obj.pk])
                cursor.execute("DELETE FROM users_user_permissions WHERE user_id = %s", [obj.pk])
                cursor.execute("DELETE FROM authtoken_token WHERE user_id = %s", [obj.pk])
                cursor.execute("DELETE FROM django_admin_log WHERE user_id = %s", [obj.pk])
                
                # Try to delete JWT tokens if tables exist
                try:
                    cursor.execute("DELETE FROM token_blacklist_blacklistedtoken WHERE token_id IN (SELECT id FROM token_blacklist_outstandingtoken WHERE user_id = %s)", [obj.pk])
                    cursor.execute("DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s", [obj.pk])
                except:
                    pass
            
            # Now delete the user
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", [obj.pk])
            
            self.message_user(
                request,
                f'User {obj.email} deleted successfully.',
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f'Error deleting user {obj.email}: {str(e)}',
                messages.ERROR
            )
    
    class Media:
        js = ('admin/js/user_admin.js',)