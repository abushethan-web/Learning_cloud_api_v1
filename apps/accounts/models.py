"""
User models for Learning Cloud application.
Optimized for handling 20M+ students with proper indexing and relationships.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from cryptography.fernet import Fernet
import os


class User(AbstractUser):
    """
    Custom User model supporting Students, Teachers, and Parents.
    """
    USER_ROLES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
        ('ADMIN', 'Administrator'),
    ]
    
    GRADE_LEVELS = [
        (1, 'Grade 1'),
        (2, 'Grade 2'),
        (3, 'Grade 3'),
        (4, 'Grade 4'),
    ]
    
    # Basic fields
    role = models.CharField(max_length=10, choices=USER_ROLES, default='STUDENT')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True, null=True)  # Optional, not unique
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Student specific fields
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    pin = models.CharField(max_length=255, blank=True, null=True)  # Encrypted PIN
    grade_level = models.IntegerField(
        choices=GRADE_LEVELS, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    grade_level_model = models.ForeignKey('GradeLevel', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    parent_email = models.EmailField(blank=True, null=True)
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Teacher specific fields
    teacher_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    subject_specialties = models.JSONField(default=list, blank=True)
    
    # Parent relationship
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['teacher_id']),
            models.Index(fields=['grade_level']),
            models.Index(fields=['grade_level_model']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def set_pin(self, pin):
        """Encrypt and store PIN"""
        if pin:
            key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
            f = Fernet(key)
            self.pin = f.encrypt(pin.encode()).decode()
    
    def check_pin(self, pin):
        """Verify PIN"""
        if not self.pin or not pin:
            return False
        try:
            key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
            f = Fernet(key)
            decrypted_pin = f.decrypt(self.pin.encode()).decode()
            return decrypted_pin == pin
        except:
            return False
    
    def is_student(self):
        return self.role == 'STUDENT'
    
    def is_teacher(self):
        return self.role == 'TEACHER'
    
    def is_parent(self):
        return self.role == 'PARENT'
    
    def get_children(self):
        """Get children for parent users"""
        if self.is_parent():
            return User.objects.filter(parent=self)
        return User.objects.none()
    
    @staticmethod
    def generate_student_id():
        """Generate a unique student ID"""
        import random
        import string
        from django.utils import timezone
        
        # Format: STU + YYYYMMDD + 4 random digits
        date_str = timezone.now().strftime('%Y%m%d')
        random_suffix = ''.join(random.choices(string.digits, k=4))
        student_id = f"STU{date_str}{random_suffix}"
        
        # Ensure uniqueness
        max_attempts = 100
        attempts = 0
        while User.objects.filter(student_id=student_id).exists() and attempts < max_attempts:
            random_suffix = ''.join(random.choices(string.digits, k=4))
            student_id = f"STU{date_str}{random_suffix}"
            attempts += 1
        
        if attempts >= max_attempts:
            # Fallback: use timestamp-based ID
            import time
            student_id = f"STU{int(time.time())}{random_suffix}"
        
        return student_id
    
    @staticmethod
    def generate_pin():
        """Generate a random 4-digit PIN"""
        import random
        return str(random.randint(1000, 9999))


class School(models.Model):
    """School model for organizing students and teachers"""
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Ethiopia')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schools'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserSession(models.Model):
    """Track user sessions for analytics and security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.login_time}"


class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['attempted_at']),
        ]
        ordering = ['-attempted_at']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username} - {status} - {self.attempted_at}"


class GradeLevel(models.Model):
    """Grade level model for organizing students by grade"""
    name = models.CharField(max_length=100)
    level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="Grade level number (0-4)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'grade_levels'
        ordering = ['level']
        indexes = [
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"


