# API Quick Reference

## Base URL
```
http://localhost:8000
```

## Authentication Flow

### 1. Sign Up
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "full_name": "Name", "password": "pass123456"}'
```

### 2. Login (Get Token)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=pass123456"
```

Returns: `{"access_token": "...", "token_type": "bearer"}`

### 3. Use Token
```bash
curl -X GET http://localhost:8000/ENDPOINT \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Common Endpoints

### Transactions
```bash
# List all
GET /transactions

# Create
POST /transactions
{"date": "2025-12-11", "amount": 50.00, "currency": "USD", "merchant": "Store", "is_expense": true}

# Get by ID
GET /transactions/{id}

# Update
PUT /transactions/{id}
{"amount": 75.00, "description": "Updated"}

# Delete
DELETE /transactions/{id}
```

### Categories
```bash
# List all
GET /categories/all

# List top-level
GET /categories

# Create
POST /categories
{"name": "Food", "icon": "🍕", "color": "#FF5733"}
```

### Accounts
```bash
# List all
GET /accounts

# Create
POST /accounts
{"name": "Cash", "account_type": "cash", "balance": 100.00, "currency": "USD"}
```

### Analytics
```bash
# Summary
GET /analytics/summary?date_from=2025-01-01&date_to=2025-12-31

# By category
GET /analytics/by-category?date_from=2025-01-01&date_to=2025-12-31
```

---

## Quick Test Script

```bash
#!/bin/bash

# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword" \
  | jq -r '.access_token')

# Create transaction
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-12-11",
    "amount": 100.00,
    "currency": "USD",
    "merchant": "Test Store",
    "is_expense": true
  }'

# List transactions
curl -X GET http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN"
```

---

## Interactive Documentation

Visit: **http://localhost:8000/docs**

1. Click "Authorize" button
2. Enter: `Bearer YOUR_TOKEN` or just `YOUR_TOKEN`
3. Click "Authorize"
4. Test endpoints interactively

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (deleted) |
| 400 | Bad Request |
| 401 | Not Authenticated |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |

---

## Environment Variables

```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
```

⚠️ Change `SECRET_KEY` in production!
