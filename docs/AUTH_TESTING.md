# Authentication Testing Guide

## Overview
JWT-based authentication is fully implemented with the following features:
- User registration (signup)
- User login with JWT token generation
- Protected endpoints using Bearer token authentication
- Password hashing with bcrypt
- Token validation and user retrieval

## Endpoints

### 1. Sign Up
**POST** `/auth/signup`

Creates a new user account.

**Request:**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "securepassword123"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-11T15:59:58.953799"
}
```

**Error Cases:**
- 400: Email already registered
- 422: Validation error (invalid email, password too short, etc.)

---

### 2. Login
**POST** `/auth/login`

Authenticates user and returns JWT access token.

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Cases:**
- 401: Incorrect email or password
- 400: Inactive user

---

### 3. Get Current User
**GET** `/auth/me`

Returns the authenticated user's profile.

**Request:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your_token_here>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-11T15:59:58.953799"
}
```

**Error Cases:**
- 401: Could not validate credentials (invalid/expired token)
- 400: Inactive user

---

## Testing Workflow

### 1. Create a Test User
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "testpassword123"
  }'
```

### 2. Login and Get Token
```bash
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123" \
  2>/dev/null | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 3. Use Token to Access Protected Endpoint
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Test Protected Transaction Endpoints
```bash
# Create a transaction (requires authentication)
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-12-11",
    "amount": 50.00,
    "currency": "USD",
    "merchant": "Test Store",
    "description": "Test purchase",
    "is_expense": true
  }'
```

---

## Configuration

JWT settings are configured in `.env`:

```env
SECRET_KEY=your-secret-key-here  # Change in production!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ Important:** Always use a strong, random SECRET_KEY in production.

---

## Security Features

✅ **Password Hashing**: Bcrypt with salt
✅ **JWT Tokens**: RS256 algorithm
✅ **Token Expiration**: Configurable (default: 30 minutes)
✅ **Email Validation**: Pydantic EmailStr
✅ **Password Requirements**: Minimum 8 characters
✅ **Protected Endpoints**: OAuth2 Bearer token authentication
✅ **User Status Check**: Active/inactive user validation

---

## Test Results

All authentication endpoints are working correctly:

- ✅ Signup creates users successfully
- ✅ Login returns valid JWT tokens
- ✅ /me endpoint validates tokens and returns user data
- ✅ Invalid credentials are rejected (401)
- ✅ Duplicate emails are rejected (400)
- ✅ Invalid tokens are rejected (401)

---

## Next Steps

To protect other endpoints:

1. Import the dependency:
```python
from app.core.security import get_current_active_user
from app.db.models import User
```

2. Add to endpoint:
```python
@router.get("/protected-endpoint")
async def protected_route(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": f"Hello {current_user.email}"}
```

For superuser-only endpoints, use `get_current_superuser` instead.
