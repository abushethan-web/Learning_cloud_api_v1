"""
URL patterns for accounts app.
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/student-register/', views.StudentRegistrationView.as_view(), name='student_register'),
    path('auth/student-login/', views.StudentLoginView.as_view(), name='student_login'),
    path('auth/teacher-login/', views.TeacherLoginView.as_view(), name='teacher_login'),
    path('auth/parent-login/', views.ParentLoginView.as_view(), name='parent_login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('change-pin/', views.ChangePinView.as_view(), name='change_pin'),
    
    # Session management
    path('sessions/', views.UserSessionsView.as_view(), name='sessions'),
    path('sessions/<int:session_id>/terminate/', views.TerminateSessionView.as_view(), name='terminate_session'),
    
    # Statistics
    path('stats/', views.user_stats, name='user_stats'),
    
    # Public endpoints
    path('schools/', views.SchoolListView.as_view(), name='schools'),
]


