"""
Views for user authentication and account management.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from .models import User, School, UserSession, LoginAttempt
from .serializers import (
    UserRegistrationSerializer, StudentRegistrationSerializer, StudentLoginSerializer, TeacherLoginSerializer,
    ParentLoginSerializer, UserProfileSerializer, ChangePasswordSerializer,
    ChangePinSerializer, SchoolSerializer, UserSessionSerializer
)
import logging

logger = logging.getLogger(__name__)


class SchoolListView(generics.ListAPIView):
    """List all active schools"""
    queryset = School.objects.filter(is_active=True)
    serializer_class = SchoolSerializer
    permission_classes = [permissions.AllowAny]


class UserRegistrationView(APIView):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Create OAuth token
                    token, created = Token.objects.get_or_create(user=user)
                    
                    # Log successful registration
                    logger.info(f"User registered: {user.username} ({user.role})")
                    
                    return Response({
                        'message': 'User registered successfully',
                        'user': UserProfileSerializer(user).data,
                        'token': token.key
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                return Response({
                    'error': 'Registration failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentRegistrationView(APIView):
    """Simplified student registration - only requires username (phone), auto-generates student ID"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Create access token (never expires)
                    token, created = Token.objects.get_or_create(user=user)
                    
                    # Create session record
                    self._create_session(request, user)
                    
                    # Log successful registration
                    logger.info(f"Student registered: {user.username} with ID: {user.student_id}")
                    
                    # Return all user data
                    user_data = UserProfileSerializer(user).data
                    school_data = SchoolSerializer(user.school).data if user.school else None
                    
                    return Response({
                        'message': 'Student registered successfully',
                        'access_token': token.key,  # Token never expires
                        'student_id': user.student_id,
                        'user': user_data,
                        'username': user.username,
                        'full_name': user.get_full_name(),
                        'email': user.email,
                        'role': user.role,
                        'grade_level': user.grade_level,
                        'school': school_data,
                        'is_verified': user.is_verified,
                        'created_at': user.created_at.isoformat() if user.created_at else None,
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Student registration error: {str(e)}")
                return Response({
                    'error': 'Registration failed',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_session(self, request, user):
        """Create user session record"""
        try:
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key or 'api',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class StudentLoginView(APIView):
    """Student login with username (phone) or student_id - NO PIN required"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Track login attempt
            self._track_login_attempt(request, user.username, True)
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Create session record
            self._create_session(request, user)
            
            logger.info(f"Student login successful: {user.student_id}")
            
            # Return all user data
            user_data = UserProfileSerializer(user).data
            school_data = SchoolSerializer(user.school).data if user.school else None
            
            return Response({
                'message': 'Login successful',
                'access_token': token.key,
                'user': user_data,
                'student_id': user.student_id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'email': user.email,
                'role': user.role,
                'grade_level': user.grade_level,
                'school': school_data,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            }, status=status.HTTP_200_OK)
        
        # Track failed login attempt
        username_or_id = request.data.get('username') or request.data.get('student_id', 'unknown')
        error_message = serializer.errors.get('non_field_errors', ['Invalid credentials'])[0] if serializer.errors.get('non_field_errors') else 'Invalid credentials'
        self._track_login_attempt(request, username_or_id, False, str(error_message))
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    def _track_login_attempt(self, request, username, success, failure_reason=''):
        """Track login attempts for security monitoring"""
        try:
            LoginAttempt.objects.create(
                username=username,
                ip_address=self._get_client_ip(request),
                success=success,
                failure_reason=failure_reason
            )
        except Exception as e:
            logger.error(f"Failed to track login attempt: {str(e)}")
    
    def _create_session(self, request, user):
        """Create user session record"""
        try:
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key or 'api',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TeacherLoginView(APIView):
    """Teacher login"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = TeacherLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            logger.info(f"Teacher login successful: {user.username}")
            
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class ParentLoginView(APIView):
    """Parent login"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ParentLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            logger.info(f"Parent login successful: {user.username}")
            
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete token
            Token.objects.filter(user=request.user).delete()
            
            # Deactivate sessions
            UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            
            logger.info(f"User logout: {request.user.username}")
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            
            # Delete existing tokens to force re-login
            Token.objects.filter(user=request.user).delete()
            
            logger.info(f"Password changed for user: {request.user.username}")
            
            return Response({
                'message': 'Password changed successfully. Please login again.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePinView(APIView):
    """Change student PIN"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_student():
            return Response({
                'error': 'Only students can change PIN'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChangePinSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            
            logger.info(f"PIN changed for student: {request.user.student_id}")
            
            return Response({
                'message': 'PIN changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionsView(generics.ListAPIView):
    """List user's active sessions"""
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-login_time')


class TerminateSessionView(APIView):
    """Terminate a specific session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
            session.is_active = False
            session.save()
            
            logger.info(f"Session terminated: {session_id} for user {request.user.username}")
            
            return Response({
                'message': 'Session terminated successfully'
            }, status=status.HTTP_200_OK)
        except UserSession.DoesNotExist:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics"""
    user = request.user
    
    stats = {
        'total_lessons': 0,
        'completed_lessons': 0,
        'total_quizzes': 0,
        'passed_quizzes': 0,
        'current_streak': 0,
        'total_points': 0,
    }
    
    # Add more stats based on user role
    if user.is_student():
        # Get student-specific stats
        pass
    elif user.is_teacher():
        # Get teacher-specific stats
        pass
    elif user.is_parent():
        # Get parent-specific stats
        pass
    
    return Response(stats, status=status.HTTP_200_OK)


