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

---

## 2. Student Login

```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU202501151234",
    "pin": "5678"
  }'
```

### Expected Response
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
- `student_id`: Use for login
- `pin`: Use for login
- `access_token`: Use for authenticated requests

### Step 2: Login (for future sessions)
```bash
curl -X POST https://learning-cloud-api-v1.onrender.com/api/auth/student-login/ \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU202501151234", "pin": "5678"}'
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

