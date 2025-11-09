# cURL Examples for Student Registration & Login

## Base URL
**https://learning-cloud-api-v1.onrender.com**

---

## 1. Register a New Student

### Basic Registration (username only)
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe"}'
```

### Registration with Full Name
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "full_name": "John Doe"
  }'
```

### Expected Response
```json
{
  "message": "Student registered successfully",
  "access_token": "abc123xyz...",
  "student_id": "STU202501151234",
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "student_id": "STU202501151234",
    "role": "STUDENT"
  },
  "username": "john_doe",
  "full_name": "John Doe",
  "email": null,
  "role": "STUDENT",
  "grade_level": null,
  "school": null,
  "is_verified": false,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## 2. Student Login (NO PIN Required)

### Login with Username (Phone Number)
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "0912345678"
  }'
```

### Login with Student ID
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU202501151234"
  }'
```

### Expected Response
```json
{
  "message": "Login successful",
  "access_token": "abc123xyz...",
  "user": {
    "id": 1,
    "username": "0912345678",
    "full_name": "John Doe",
    "student_id": "STU202501151234",
    "role": "STUDENT",
    "email": null,
    "grade_level": null,
    "school": null,
    "is_verified": false,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "student_id": "STU202501151234",
  "username": "0912345678",
  "full_name": "John Doe",
  "email": null,
  "role": "STUDENT",
  "grade_level": null,
  "school": null,
  "is_verified": false,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

## 3. Get User Profile (Authenticated)

```bash
curl -X GET https://learning-cloud-api-v1.onrender.com/api/profile/ \
  -H "Authorization: Token your_access_token_here"
```

---

## Complete Example Workflow

### Step 1: Register
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test_student_001", "full_name": "Test Student"}'
```

**Save the response:**
- `student_id`: Use for login (optional)
- `username`: Use for login (phone number)
- `access_token`: Use for authenticated requests (token never expires)

### Step 2: Login (for future sessions) - NO PIN Required
```bash
# Login with username (phone number)
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "0912345678"}'

# OR login with student_id
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU202501151234"}'
```

### Step 3: Use Access Token
```bash
curl -X GET https://learning-cloud-api-v1.onrender.com/api/profile/ \
  -H "Authorization: Token abc123xyz..."
```

---

## Windows PowerShell (Alternative)

If you're using Windows PowerShell, use this format:

```powershell
Invoke-RestMethod -Uri "https://learning-cloud-api-v1.onrender.com/api/auth/student-register/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username": "john_doe", "full_name": "John Doe"}'
```

---

## Testing Tips

1. **Pretty Print JSON Response:**
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user"}' | python -m json.tool
```

2. **Save Response to File:**
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user"}' > response.json
```

3. **Verbose Output (for debugging):**
```bash
curl -v -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user"}'
```

