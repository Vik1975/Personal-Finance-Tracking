# API Quick Reference

## Base URL
```
http://localhost:8000
```

---

## 🔐 Authentication Endpoints

### POST /auth/signup
**Description:** Create a new user account
**Authentication:** None required
**Request Body:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securePassword123"
}
```
**Example:**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "full_name": "John Doe", "password": "securePassword123"}'
```

### POST /auth/login
**Description:** Login and receive JWT access token
**Authentication:** None required
**Request Body (form-encoded):**
- `username`: email address
- `password`: user password

**Example:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securePassword123"
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### GET /auth/me
**Description:** Get current user information
**Authentication:** Required (Bearer token)
**Example:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📄 Document Upload Endpoints

### POST /uploads
**Description:** Upload a receipt/invoice document (PDF, JPG, PNG) for OCR processing
**Authentication:** Required
**Request:** Multipart form-data with file
**Example:**
```bash
curl -X POST http://localhost:8000/uploads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@receipt.pdf"
```
**Response:**
```json
{
  "id": 1,
  "filename": "receipt.pdf",
  "status": "queued",
  "created_at": "2025-12-11T12:00:00"
}
```

### GET /uploads/list
**Description:** List all uploaded documents for current user
**Authentication:** Required
**Example:**
```bash
curl -X GET http://localhost:8000/uploads/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GET /uploads/{document_id}
**Description:** Get document details including OCR results and processing status
**Authentication:** Required
**Path Parameter:** `document_id` (integer, e.g., 1, 2, 3)
**Example:**
```bash
curl -X GET http://localhost:8000/uploads/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### DELETE /uploads/{document_id}
**Description:** Delete a document and its associated file
**Authentication:** Required
**Path Parameter:** `document_id` (integer)
**Example:**
```bash
curl -X DELETE http://localhost:8000/uploads/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /uploads/{document_id}/process
**Description:** Manually trigger reprocessing of a document
**Authentication:** Required
**Path Parameter:** `document_id` (integer)
**Example:**
```bash
curl -X POST http://localhost:8000/uploads/1/process \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 💰 Transaction Endpoints

### GET /transactions
**Description:** List all transactions for current user
**Authentication:** Required
**Query Parameters (optional):**
- `skip`: number of records to skip (default: 0)
- `limit`: max records to return (default: 100)
- `category_id`: filter by category
- `account_id`: filter by account
- `start_date`: filter from date (YYYY-MM-DD)
- `end_date`: filter to date (YYYY-MM-DD)

**Example:**
```bash
curl -X GET "http://localhost:8000/transactions?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /transactions
**Description:** Create a new transaction manually
**Authentication:** Required
**Request Body:**
```json
{
  "date": "2025-12-11",
  "amount": 50.00,
  "currency": "USD",
  "merchant": "Coffee Shop",
  "description": "Morning coffee",
  "is_expense": true,
  "category_id": 1,
  "account_id": 1
}
```
**Example:**
```bash
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-12-11", "amount": 50.00, "merchant": "Coffee Shop", "is_expense": true}'
```

### GET /transactions/{transaction_id}
**Description:** Get a specific transaction by ID
**Authentication:** Required
**Path Parameter:** `transaction_id` (integer)
**Example:**
```bash
curl -X GET http://localhost:8000/transactions/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### PUT /transactions/{transaction_id}
**Description:** Update an existing transaction
**Authentication:** Required
**Path Parameter:** `transaction_id` (integer)
**Request Body:** (partial updates allowed)
```json
{
  "amount": 75.00,
  "description": "Updated description",
  "category_id": 2
}
```
**Example:**
```bash
curl -X PUT http://localhost:8000/transactions/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 75.00, "description": "Updated"}'
```

### DELETE /transactions/{transaction_id}
**Description:** Delete a transaction
**Authentication:** Required
**Path Parameter:** `transaction_id` (integer)
**Example:**
```bash
curl -X DELETE http://localhost:8000/transactions/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📂 Category Endpoints

### GET /categories
**Description:** List all top-level categories (no parent)
**Authentication:** Required
**Example:**
```bash
curl -X GET http://localhost:8000/categories \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GET /categories/all
**Description:** List all categories including subcategories
**Authentication:** Required
**Example:**
```bash
curl -X GET http://localhost:8000/categories/all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /categories
**Description:** Create a new category
**Authentication:** Required
**Request Body:**
```json
{
  "name": "Groceries",
  "icon": "🛒",
  "color": "#4CAF50",
  "parent_id": 1
}
```
**Example:**
```bash
curl -X POST http://localhost:8000/categories \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries", "icon": "🛒", "color": "#4CAF50"}'
```

### GET /categories/{category_id}
**Description:** Get a specific category by ID
**Authentication:** Required
**Path Parameter:** `category_id` (integer)
**Example:**
```bash
curl -X GET http://localhost:8000/categories/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### PUT /categories/{category_id}
**Description:** Update a category
**Authentication:** Required
**Path Parameter:** `category_id` (integer)
**Request Body:** (partial updates allowed)
```json
{
  "name": "Food & Groceries",
  "color": "#FF5722"
}
```

### DELETE /categories/{category_id}
**Description:** Delete a category
**Authentication:** Required
**Path Parameter:** `category_id` (integer)

---

## 🏦 Account Endpoints

### GET /accounts
**Description:** List all accounts for current user
**Authentication:** Required
**Example:**
```bash
curl -X GET http://localhost:8000/accounts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /accounts
**Description:** Create a new account
**Authentication:** Required
**Request Body:**
```json
{
  "name": "Main Checking",
  "account_type": "checking",
  "balance": 1000.00,
  "currency": "USD",
  "description": "Primary checking account"
}
```
**Account Types:** `checking`, `savings`, `credit_card`, `cash`, `investment`
**Example:**
```bash
curl -X POST http://localhost:8000/accounts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cash", "account_type": "cash", "balance": 100.00, "currency": "USD"}'
```

### GET /accounts/{account_id}
**Description:** Get a specific account by ID
**Authentication:** Required
**Path Parameter:** `account_id` (integer)

### PUT /accounts/{account_id}
**Description:** Update an account
**Authentication:** Required
**Path Parameter:** `account_id` (integer)
**Request Body:** (partial updates allowed)
```json
{
  "name": "Updated Account Name",
  "balance": 1500.00
}
```

### DELETE /accounts/{account_id}
**Description:** Delete an account
**Authentication:** Required
**Path Parameter:** `account_id` (integer)

---

## 💵 Budget Endpoints

### GET /budgets
**Description:** List all budgets for current user
**Authentication:** Required
**Example:**
```bash
curl -X GET http://localhost:8000/budgets \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /budgets
**Description:** Create a new budget
**Authentication:** Required
**Request Body:**
```json
{
  "name": "Monthly Food Budget",
  "amount": 500.00,
  "period": "month",
  "category_id": 1,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```
**Period Options:** `day`, `week`, `month`, `year`
**Example:**
```bash
curl -X POST http://localhost:8000/budgets \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Food Budget", "amount": 500.00, "period": "month", "category_id": 1}'
```

### GET /budgets/{budget_id}
**Description:** Get a specific budget by ID
**Authentication:** Required
**Path Parameter:** `budget_id` (integer)

### GET /budgets/{budget_id}/status
**Description:** Get budget status including spent amount and remaining balance
**Authentication:** Required
**Path Parameter:** `budget_id` (integer)
**Example:**
```bash
curl -X GET http://localhost:8000/budgets/1/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### PUT /budgets/{budget_id}
**Description:** Update a budget
**Authentication:** Required
**Path Parameter:** `budget_id` (integer)

### DELETE /budgets/{budget_id}
**Description:** Delete a budget
**Authentication:** Required
**Path Parameter:** `budget_id` (integer)

---

## 📊 Analytics Endpoints

### GET /analytics/summary
**Description:** Get financial summary with total income, expenses, and balance
**Authentication:** Required
**Query Parameters (optional):**
- `date_from`: start date in YYYY-MM-DD format (default: first day of current month)
- `date_to`: end date in YYYY-MM-DD format (default: today)
- `account_id`: filter by specific account

**Example:**
```bash
curl -X GET "http://localhost:8000/analytics/summary?date_from=2025-11-01&date_to=2025-11-30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response:**
```json
{
  "total_income": "1500.00",
  "total_expenses": "850.00",
  "balance": "650.00",
  "transactions_count": 25,
  "period_start": "2025-11-01",
  "period_end": "2025-11-30"
}
```

### GET /analytics/categories
**Description:** Get spending breakdown by category
**Authentication:** Required
**Query Parameters (optional):**
- `date_from`: start date (YYYY-MM-DD)
- `date_to`: end date (YYYY-MM-DD)
- `account_id`: filter by account

**Example:**
```bash
curl -X GET "http://localhost:8000/analytics/categories?date_from=2025-11-01&date_to=2025-11-30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response:**
```json
[
  {
    "category_id": 1,
    "category_name": "Food & Dining",
    "total": "350.00",
    "count": 12,
    "percentage": 41.2
  },
  {
    "category_id": null,
    "category_name": "Uncategorized",
    "total": "100.50",
    "count": 3,
    "percentage": 11.8
  }
]
```

### GET /analytics/top-merchants
**Description:** Get top spending merchants
**Authentication:** Required
**Query Parameters (optional):**
- `limit`: number of merchants to return (default: 10)
- `date_from`: start date (YYYY-MM-DD)
- `date_to`: end date (YYYY-MM-DD)

**Example:**
```bash
curl -X GET "http://localhost:8000/analytics/top-merchants?limit=5&date_from=2025-11-01&date_to=2025-11-30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GET /analytics/trends
**Description:** Get spending trends over time (daily/weekly/monthly)
**Authentication:** Required
**Query Parameters (optional):**
- `period`: aggregation period - `day`, `week`, `month`, or `year` (default: `month`)
- `date_from`: start date (YYYY-MM-DD)
- `date_to`: end date (YYYY-MM-DD)

**Example:**
```bash
curl -X GET "http://localhost:8000/analytics/trends?period=week&date_from=2025-11-01&date_to=2025-11-30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Utility Endpoints

### GET /
**Description:** Root endpoint with API information
**Authentication:** None required
**Example:**
```bash
curl -X GET http://localhost:8000/
```

### GET /health
**Description:** Health check endpoint
**Authentication:** None required
**Example:**
```bash
curl -X GET http://localhost:8000/health
```
**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### GET /version
**Description:** Get API version information
**Authentication:** None required
**Example:**
```bash
curl -X GET http://localhost:8000/version
```

---

## 📝 Quick Test Script

```bash
#!/bin/bash

# 1. Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword" \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Upload a receipt
curl -X POST http://localhost:8000/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@receipt.pdf"

# 3. List all documents
curl -X GET http://localhost:8000/uploads/list \
  -H "Authorization: Bearer $TOKEN"

# 4. Create a manual transaction
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

# 5. List all transactions
curl -X GET http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN"

# 6. Get analytics summary
curl -X GET "http://localhost:8000/analytics/summary?date_from=2025-12-01&date_to=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"

# 7. Get category breakdown
curl -X GET "http://localhost:8000/analytics/categories?date_from=2025-12-01&date_to=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🌐 Interactive Documentation

### Swagger UI
Visit: **http://localhost:8000/docs**

1. Click "Authorize" button (🔒 icon)
2. Enter your token (just the token value, not "Bearer")
3. Click "Authorize"
4. Test endpoints interactively with live examples

### ReDoc
Visit: **http://localhost:8000/redoc**
- Alternative documentation viewer
- Better for reading and understanding API structure

---

## ⚠️ Common Input Formats

### Date Format
All dates must be in **ISO 8601 format: YYYY-MM-DD**
```
Valid:   2025-12-11
Invalid: 12/11/2025, 11-12-2025, Dec 11 2025
```

### Amount/Currency
- Amounts: Decimal numbers (e.g., `100.00`, `50.5`, `1234.56`)
- Currency: 3-letter ISO code (e.g., `USD`, `EUR`, `GBP`)

### Colors
Colors should be in **hex format** with `#` prefix
```
Valid:   #FF5733, #4CAF50, #000000
Invalid: red, rgb(255,0,0), FF5733
```

### Account Types
Valid values: `checking`, `savings`, `credit_card`, `cash`, `investment`

### Period Types
Valid values: `day`, `week`, `month`, `year`

---

## ❌ HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Resource deleted successfully |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Request body failed validation |
| 500 | Internal Server Error | Server error (contact support) |

---

## 🔑 Authentication Header Format

After login, include the token in all requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Note:** The token expires after 30 minutes by default. You'll need to login again to get a new token.

---

## 🐛 Troubleshooting

### "Could not validate credentials"
- Token expired (login again)
- Token not included in Authorization header
- Wrong token format (should be `Bearer YOUR_TOKEN`)

### "Document status: queued"
- Document is waiting for Celery worker to process
- Usually processes within 1-10 seconds
- Large PDFs may take 30+ seconds
- Check status with `GET /uploads/{document_id}`

### "Document status: failed"
- Check `error_message` field in response
- Common causes: Corrupt file, unsupported format, OCR failure
- Can retry with `POST /uploads/{document_id}/process`

### Empty analytics data
- Check date range (default is current month only)
- Use `date_from` and `date_to` parameters to expand range
- Example: `?date_from=2025-01-01&date_to=2025-12-31`

---

## 🔒 Environment Variables

```env
# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/finance_tracker

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

⚠️ **IMPORTANT:** Always change `SECRET_KEY` in production environments!
