from django.urls import path
from . import views
from . import forgot_password_views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh/', views.refresh_token_view, name='refresh'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Forgot password endpoints
    path('forgot-password/request/', forgot_password_views.request_password_reset, name='request-password-reset'),
    path('forgot-password/verify-otp/', forgot_password_views.verify_otp, name='verify-otp'),
    path('forgot-password/reset/', forgot_password_views.reset_password, name='reset-password'),
]
