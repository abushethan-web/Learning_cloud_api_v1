"""
Serializers for User accounts and authentication.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, School, UserSession, LoginAttempt


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model"""
    
    class Meta:
        model = School
        fields = ['id', 'name', 'address', 'city', 'country', 'is_active']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'grade_level',
            'student_id', 'pin', 'parent_email', 'school'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'pin': {'write_only': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_student_id(self, value):
        if value and User.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("Student ID already exists")
        return value
    
    def validate_teacher_id(self, value):
        if value and User.objects.filter(teacher_id=value).exists():
            raise serializers.ValidationError("Teacher ID already exists")
        return value
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        pin = validated_data.pop('pin', None)
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        if pin:
            user.set_pin(pin)
            user.save()
        
        return user


class StudentLoginSerializer(serializers.Serializer):
    """Serializer for student login with username (phone) or student_id - NO PIN required"""
    student_id = serializers.CharField(max_length=20, required=False)
    username = serializers.CharField(max_length=150, required=False)
    
    def validate(self, attrs):
        student_id = attrs.get('student_id')
        username = attrs.get('username')
        
        user = None
        
        # Login with username (phone number) or student_id - no PIN needed
        if username:
            # Strip whitespace and normalize username
            username = username.strip()
            
            # Try exact match first
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Try case-insensitive match
                try:
                    user = User.objects.get(username__iexact=username)
                except User.DoesNotExist:
                    # Check if any user with similar username exists (for debugging)
                    all_students = User.objects.filter(role='STUDENT').values_list('username', flat=True)[:10]
                    similar_users = User.objects.filter(username__icontains=username[:5] if len(username) >= 5 else username)[:5]
                    
                    error_msg = f"Username '{username}' not found. Please register first."
                    if similar_users.exists():
                        error_msg += f" (Found {similar_users.count()} similar usernames)"
                    if all_students:
                        error_msg += f" (Sample usernames in DB: {list(all_students)[:3]})"
                    
                    raise serializers.ValidationError({
                        'non_field_errors': [error_msg]
                    })
            
            # Then check if it's a student and active
            if user.role != 'STUDENT':
                raise serializers.ValidationError({
                    'non_field_errors': [f"User is not a student account. Current role: {user.role}"]
                })
            if not user.is_active:
                raise serializers.ValidationError({
                    'non_field_errors': ["Account is deactivated"]
                })
        elif student_id:
            try:
                # First try to get user by student_id only
                user = User.objects.get(student_id=student_id)
                
                # Then check if it's a student and active
                if user.role != 'STUDENT':
                    raise serializers.ValidationError({
                        'non_field_errors': ["User is not a student account"]
                    })
                if not user.is_active:
                    raise serializers.ValidationError({
                        'non_field_errors': ["Account is deactivated"]
                    })
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'non_field_errors': [f"Student ID '{student_id}' not found. Please register first."]
                })
        else:
            raise serializers.ValidationError({
                'non_field_errors': ["Either username or student_id is required"]
            })
        
        attrs['user'] = user
        return attrs


class TeacherLoginSerializer(serializers.Serializer):
    """Serializer for teacher login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_teacher():
                raise serializers.ValidationError("Access denied. Teacher account required.")
            if not user.is_active:
                raise serializers.ValidationError("Account is deactivated")
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Username and password are required")


class ParentLoginSerializer(serializers.Serializer):
    """Serializer for parent login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_parent():
                raise serializers.ValidationError("Access denied. Parent account required.")
            if not user.is_active:
                raise serializers.ValidationError("Account is deactivated")
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Username and password are required")


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile - returns all user data"""
    school = SchoolSerializer(read_only=True)
    school_id = serializers.IntegerField(write_only=True, required=False)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'grade_level', 'student_id', 'teacher_id', 'school', 'school_id',
            'subject_specialties', 'is_verified', 'last_login', 'children',
            'created_at', 'updated_at', 'parent_email', 'is_active'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'last_login', 'updated_at']
    
    def get_children(self, obj):
        if obj.is_parent():
            children = obj.get_children()
            return UserProfileSerializer(children, many=True, context=self.context).data
        return []
    
    def update(self, instance, validated_data):
        school_id = validated_data.pop('school_id', None)
        if school_id:
            try:
                school = School.objects.get(id=school_id)
                instance.school = school
            except School.DoesNotExist:
                pass
        
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ChangePinSerializer(serializers.Serializer):
    """Serializer for PIN change (students only)"""
    old_pin = serializers.CharField()
    new_pin = serializers.CharField(min_length=4, max_length=10)
    confirm_pin = serializers.CharField()
    
    def validate_old_pin(self, value):
        user = self.context['request'].user
        if not user.check_pin(value):
            raise serializers.ValidationError("Old PIN is incorrect")
        return value
    
    def validate(self, attrs):
        if attrs['new_pin'] != attrs['confirm_pin']:
            raise serializers.ValidationError("New PINs don't match")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_pin(self.validated_data['new_pin'])
        user.save()
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = UserSession
        fields = ['id', 'user', 'ip_address', 'login_time', 'last_activity', 'is_active']
        read_only_fields = ['id', 'user', 'ip_address', 'login_time', 'last_activity']


class LoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer for login attempts (admin only)"""
    
    class Meta:
        model = LoginAttempt
        fields = ['id', 'username', 'ip_address', 'success', 'failure_reason', 'attempted_at']
        read_only_fields = ['id', 'attempted_at']


class StudentRegistrationSerializer(serializers.Serializer):
    """Simplified serializer for student registration - only requires username (phone number)"""
    username = serializers.CharField(
        max_length=150,
        help_text="Username (phone number) for the student account"
    )
    full_name = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        help_text="Full name (optional). If provided, will be split into first_name and last_name"
    )
    
    def validate_username(self, value):
        """Check if username already exists"""
        # Strip whitespace and normalize
        value = value.strip() if value else value
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def create(self, validated_data):
        """Create a new student user with auto-generated student ID - NO PIN needed"""
        username = validated_data['username'].strip()  # Ensure no whitespace
        full_name = validated_data.get('full_name', '').strip()
        
        # Split full name if provided
        if full_name:
            name_parts = full_name.split(maxsplit=1)
            first_name = name_parts[0] if len(name_parts) > 0 else username
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        else:
            # Use username as first name if no full name provided
            first_name = username
            last_name = ''
        
        # Generate student ID
        student_id = User.generate_student_id()
        
        # Create user with auto-generated password (no PIN needed for login)
        # Generate a random password for Django's user system
        import secrets
        password = secrets.token_urlsafe(32)
        
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='STUDENT',
            student_id=student_id,
            is_active=True
        )
        
        # Log the created user for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Created student user: username='{user.username}', student_id='{user.student_id}', id={user.id}, role='{user.role}'")
        
        return user


