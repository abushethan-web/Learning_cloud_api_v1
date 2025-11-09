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
    """Serializer for student login with Student ID and PIN"""
    student_id = serializers.CharField(max_length=20)
    pin = serializers.CharField(max_length=10)
    
    def validate(self, attrs):
        student_id = attrs.get('student_id')
        pin = attrs.get('pin')
        
        if not student_id or not pin:
            raise serializers.ValidationError("Student ID and PIN are required")
        
        try:
            user = User.objects.get(student_id=student_id, role='STUDENT', is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid Student ID")
        
        if not user.check_pin(pin):
            raise serializers.ValidationError("Invalid PIN")
        
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
    """Serializer for user profile"""
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
            'created_at'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'last_login']
    
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
    """Simplified serializer for student registration - only requires username"""
    username = serializers.CharField(
        max_length=150,
        help_text="Username for the student account"
    )
    full_name = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        help_text="Full name (optional). If provided, will be split into first_name and last_name"
    )
    
    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def create(self, validated_data):
        """Create a new student user with auto-generated student ID and PIN"""
        username = validated_data['username']
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
        
        # Generate PIN
        pin = User.generate_pin()
        
        # Create user with auto-generated password (students use PIN for login)
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
        
        # Set encrypted PIN
        user.set_pin(pin)
        user.save()
        
        # Store PIN in the serializer context for response (not saved to user)
        self.context['generated_pin'] = pin
        
        return user


