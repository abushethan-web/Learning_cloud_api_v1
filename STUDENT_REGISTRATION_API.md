# Student Registration & Login API

## Base URL
**https://learning-cloud-api-v1.onrender.com**

## Endpoints

### 1. Student Registration
**POST** `/api/auth/student-register/`

### 2. Student Login
**POST** `/api/auth/student-login/`

## Description

Simplified student registration endpoint that only requires a username. The system automatically:
- Generates a unique student ID (format: `STU{YYYYMMDD}{4digits}`)
- Generates a random 4-digit PIN
- Sets role to STUDENT
- Creates an access token for immediate use

## Request

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
{
  "username": "john_doe",
  "full_name": "John Doe"  // Optional - if not provided, username will be used as first name
}
```

### Minimal Request (username only)
```json
{
  "username": "john_doe"
}
```

## Response

### Success (201 Created)
```json
{
  "message": "Student registered successfully",
  "student_id": "STU202501151234",
  "pin": "5678",
  "access_token": "your_access_token_here",
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "student_id": "STU202501151234",
    "role": "STUDENT"
  }
}
```

### Error (400 Bad Request)
```json
{
  "username": ["Username already exists"]
}
```

## Example Usage

### cURL - Registration
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "full_name": "John Doe"
  }'
```

### Python (requests) - Registration
```python
import requests

BASE_URL = "https://learning-cloud-api-v1.onrender.com"

# Registration
registration_url = f"{BASE_URL}/api/auth/student-register/"
data = {
    "username": "john_doe",
    "full_name": "John Doe"  # Optional
}

response = requests.post(registration_url, json=data)
result = response.json()

print(f"Student ID: {result['student_id']}")
print(f"PIN: {result['pin']}")
print(f"Access Token: {result['access_token']}")

# Save these for login
student_id = result['student_id']
pin = result['pin']
access_token = result['access_token']
```

### JavaScript (fetch) - Registration
```javascript
const BASE_URL = 'https://learning-cloud-api-v1.onrender.com';

// Registration
fetch(`${BASE_URL}/api/auth/student-register/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'john_doe',
    full_name: 'John Doe'  // Optional
  })
})
.then(response => response.json())
.then(data => {
  console.log('Student ID:', data.student_id);
  console.log('PIN:', data.pin);
  console.log('Access Token:', data.access_token);
  
  // Save these for login
  localStorage.setItem('student_id', data.student_id);
  localStorage.setItem('pin', data.pin);
  localStorage.setItem('access_token', data.access_token);
});
```

### cURL - Login
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU202501151234",
    "pin": "5678"
  }'
```

### Python (requests) - Login
```python
import requests

BASE_URL = "https://learning-cloud-api-v1.onrender.com"

# Login
login_url = f"{BASE_URL}/api/auth/student-login/"
login_data = {
    "student_id": "STU202501151234",  # Use the student_id from registration
    "pin": "5678"  # Use the PIN from registration
}

response = requests.post(login_url, json=login_data)
result = response.json()

print(f"Access Token: {result['token']}")
print(f"User: {result['user']}")

# Use this token for authenticated requests
access_token = result['token']
```

### JavaScript (fetch) - Login
```javascript
const BASE_URL = 'https://learning-cloud-api-v1.onrender.com';

// Login
fetch(`${BASE_URL}/api/auth/student-login/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    student_id: 'STU202501151234',  // Use the student_id from registration
    pin: '5678'  // Use the PIN from registration
  })
})
.then(response => response.json())
.then(data => {
  console.log('Access Token:', data.token);
  console.log('User:', data.user);
  
  // Save token for authenticated requests
  localStorage.setItem('access_token', data.token);
});
```

## Important Notes

1. **Student ID Format**: `STU{YYYYMMDD}{4digits}`
   - Example: `STU202501151234`
   - Automatically generated and guaranteed to be unique

2. **PIN**: 
   - 4-digit random PIN (1000-9999)
   - Returned only once during registration
   - Encrypted and stored in database
   - Used for login via `/api/auth/student-login/`

3. **Access Token**:
   - Immediately usable for authenticated requests
   - Include in headers: `Authorization: Token your_access_token_here`

4. **Username**:
   - Must be unique
   - Required field
   - Used for account identification

5. **Full Name**:
   - Optional field
   - If provided, will be split into first_name and last_name
   - If not provided, username will be used as first_name

## Using the Access Token

After registration or login, use the access token for authenticated requests:

```bash
curl -X GET https://learning-cloud-api-v1.onrender.com/api/profile/ \
  -H "Authorization: Token your_access_token_here"
```

## Complete Student Flow

### Step 1: Register a New Student
```bash
POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/
Content-Type: application/json

{
  "username": "john_doe",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "message": "Student registered successfully",
  "student_id": "STU202501151234",
  "pin": "5678",
  "access_token": "abc123xyz...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "student_id": "STU202501151234",
    "role": "STUDENT"
  }
}
```

**Important:** Save the `student_id` and `pin` - you'll need them for future logins!

### Step 2: Login (for future sessions)
```bash
POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/
Content-Type: application/json

{
  "student_id": "STU202501151234",
  "pin": "5678"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "token": "abc123xyz...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "student_id": "STU202501151234",
    "role": "STUDENT"
  }
}
```

### Step 3: Use Access Token for Authenticated Requests
```bash
GET https://learning-cloud-api-v1.onrender.com/api/profile/
Authorization: Token abc123xyz...
```

## Rate Limiting

- Maximum 20 registrations per hour per IP address

## Auto-Generated Fields

The following fields are automatically set:
- `role`: "STUDENT"
- `student_id`: Auto-generated unique ID
- `pin`: Auto-generated 4-digit PIN (encrypted)
- `is_active`: True
- `password`: Auto-generated secure password (students use PIN for login)
- `first_name` and `last_name`: From full_name or username

## Error Handling

### Username Already Exists
```json
{
  "username": ["Username already exists"]
}
```

### Invalid Username Format
```json
{
  "username": ["This field may not be blank."]
}
```

### Invalid Login Credentials
```json
{
  "non_field_errors": ["Invalid Student ID"]  // or "Invalid PIN"
}
```

## Quick Reference

### Registration Endpoint
- **URL**: `https://learning-cloud-api-v1.onrender.com/api/auth/student-register/`
- **Method**: POST
- **Required**: `username`
- **Optional**: `full_name`

### Login Endpoint
- **URL**: `https://learning-cloud-api-v1.onrender.com/api/auth/student-login/`
- **Method**: POST
- **Required**: `student_id`, `pin`

### Profile Endpoint (Authenticated)
- **URL**: `https://learning-cloud-api-v1.onrender.com/api/profile/`
- **Method**: GET
- **Headers**: `Authorization: Token your_access_token_here`

## Testing with Postman

### Registration Request
1. Method: **POST**
2. URL: `https://learning-cloud-api-v1.onrender.com/api/auth/student-register/`
3. Headers:
   - `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "username": "test_student_001",
  "full_name": "Test Student"
}
```

### Login Request
1. Method: **POST**
2. URL: `https://learning-cloud-api-v1.onrender.com/api/auth/student-login/`
3. Headers:
   - `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "student_id": "STU202501151234",
  "pin": "5678"
}
```

### Authenticated Request
1. Method: **GET**
2. URL: `https://learning-cloud-api-v1.onrender.com/api/profile/`
3. Headers:
   - `Authorization: Token your_access_token_here`

## Security Notes

1. **PIN Security**: The PIN is encrypted before storage using Fernet encryption
2. **Token Security**: Access tokens should be stored securely on the client side
3. **Rate Limiting**: Registration is rate-limited to prevent abuse
4. **Session Tracking**: User sessions are automatically tracked for security

