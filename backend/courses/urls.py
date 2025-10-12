from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course CRUD operations (admin only)
    path('', views.CourseListView.as_view(), name='course-list'),
    path('create/', views.CourseCreateView.as_view(), name='course-create'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('<int:pk>/update/', views.CourseUpdateView.as_view(), name='course-update'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course-delete'),

    # Teacher-specific views
    path('teacher/courses/', views.teacher_courses_view, name='teacher-courses'),

    # Enrollment management (admin only)
    path('enroll/', views.EnrollmentCreateView.as_view(), name='enrollment-create'),
    path('enroll/<int:pk>/delete/', views.EnrollmentDeleteView.as_view(), name='enrollment-delete'),

    # Course enrollments
    path('<int:course_id>/enrollments/', views.CourseEnrollmentsView.as_view(), name='course-enrollments'),
]
