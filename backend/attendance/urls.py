from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Attendance session management
    path('sessions/', views.AttendanceSessionListView.as_view(), name='session-list'),
    path('sessions/create/', views.AttendanceSessionCreateView.as_view(), name='session-create'),
    path('sessions/<int:pk>/', views.AttendanceSessionDetailView.as_view(), name='session-detail'),
    path('sessions/<int:session_id>/end/', views.end_attendance_session, name='session-end'),
    path('sessions/active/', views.get_active_sessions, name='active-sessions'),
    
    # Attendance marking
    path('mark/', views.mark_attendance, name='mark-attendance'),
    
    # Student notifications
    path('notifications/', views.get_student_notifications, name='student-notifications'),
    
    # Statistics and reporting
    path('stats/', views.get_attendance_stats, name='attendance-stats'),
]
