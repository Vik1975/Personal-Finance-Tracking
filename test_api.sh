#!/bin/bash

# Personal Finance Tracker API Test Script
# Tests authentication and protected endpoints

set -e

BASE_URL="http://localhost:8000"
EMAIL="testuser_$(date +%s)@example.com"
PASSWORD="SecurePassword123"

echo "========================================"
echo "Personal Finance Tracker - API Test"
echo "========================================"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Signup
echo -e "${YELLOW}Test 1: User Signup${NC}"
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"full_name\": \"Test User\", \"password\": \"$PASSWORD\"}")

USER_ID=$(echo $SIGNUP_RESPONSE | jq -r '.id')
if [ "$USER_ID" != "null" ]; then
  echo -e "${GREEN}✓ Signup successful. User ID: $USER_ID${NC}"
else
  echo -e "${RED}✗ Signup failed${NC}"
  echo $SIGNUP_RESPONSE | jq .
  exit 1
fi
echo

# Test 2: Login
echo -e "${YELLOW}Test 2: User Login${NC}"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo -e "${GREEN}✓ Login successful${NC}"
  echo "Token: ${TOKEN:0:30}..."
else
  echo -e "${RED}✗ Login failed${NC}"
  exit 1
fi
echo

# Test 3: Get current user
echo -e "${YELLOW}Test 3: Get Current User (/auth/me)${NC}"
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")

ME_EMAIL=$(echo $ME_RESPONSE | jq -r '.email')
if [ "$ME_EMAIL" == "$EMAIL" ]; then
  echo -e "${GREEN}✓ User profile retrieved successfully${NC}"
else
  echo -e "${RED}✗ Failed to get user profile${NC}"
  exit 1
fi
echo

# Test 4: Protected endpoint without auth (should fail)
echo -e "${YELLOW}Test 4: Access Protected Endpoint Without Auth${NC}"
UNAUTH_RESPONSE=$(curl -s -X GET "$BASE_URL/transactions")
DETAIL=$(echo $UNAUTH_RESPONSE | jq -r '.detail')

if [ "$DETAIL" == "Not authenticated" ]; then
  echo -e "${GREEN}✓ Correctly rejected unauthenticated request${NC}"
else
  echo -e "${RED}✗ Endpoint not properly protected${NC}"
  exit 1
fi
echo

# Test 5: Create transaction
echo -e "${YELLOW}Test 5: Create Transaction${NC}"
TRANSACTION=$(curl -s -X POST "$BASE_URL/transactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-12-11",
    "amount": 150.75,
    "currency": "USD",
    "merchant": "Test Merchant",
    "description": "API Test Transaction",
    "is_expense": true
  }')

TRANSACTION_ID=$(echo $TRANSACTION | jq -r '.id')
if [ "$TRANSACTION_ID" != "null" ]; then
  echo -e "${GREEN}✓ Transaction created. ID: $TRANSACTION_ID${NC}"
else
  echo -e "${RED}✗ Failed to create transaction${NC}"
  echo $TRANSACTION | jq .
  exit 1
fi
echo

# Test 6: List transactions
echo -e "${YELLOW}Test 6: List Transactions${NC}"
TRANSACTIONS=$(curl -s -X GET "$BASE_URL/transactions" \
  -H "Authorization: Bearer $TOKEN")

COUNT=$(echo $TRANSACTIONS | jq 'length')
if [ "$COUNT" -gt "0" ]; then
  echo -e "${GREEN}✓ Retrieved $COUNT transaction(s)${NC}"
else
  echo -e "${RED}✗ No transactions found${NC}"
  exit 1
fi
echo

# Test 7: Get transaction by ID
echo -e "${YELLOW}Test 7: Get Transaction by ID${NC}"
TRANSACTION_DETAIL=$(curl -s -X GET "$BASE_URL/transactions/$TRANSACTION_ID" \
  -H "Authorization: Bearer $TOKEN")

RETRIEVED_ID=$(echo $TRANSACTION_DETAIL | jq -r '.id')
if [ "$RETRIEVED_ID" == "$TRANSACTION_ID" ]; then
  echo -e "${GREEN}✓ Transaction retrieved successfully${NC}"
else
  echo -e "${RED}✗ Failed to retrieve transaction${NC}"
  exit 1
fi
echo

# Test 8: Update transaction
echo -e "${YELLOW}Test 8: Update Transaction${NC}"
UPDATED=$(curl -s -X PUT "$BASE_URL/transactions/$TRANSACTION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200.00,
    "description": "Updated Test Transaction"
  }')

NEW_AMOUNT=$(echo $UPDATED | jq -r '.amount')
if [ "$NEW_AMOUNT" == "200.00" ]; then
  echo -e "${GREEN}✓ Transaction updated successfully${NC}"
else
  echo -e "${RED}✗ Failed to update transaction${NC}"
  exit 1
fi
echo

# Test 9: Get categories
echo -e "${YELLOW}Test 9: List Categories${NC}"
CATEGORIES=$(curl -s -X GET "$BASE_URL/categories/all" \
  -H "Authorization: Bearer $TOKEN")

CAT_COUNT=$(echo $CATEGORIES | jq 'length')
if [ "$CAT_COUNT" -gt "0" ]; then
  echo -e "${GREEN}✓ Retrieved $CAT_COUNT categories${NC}"
else
  echo -e "${RED}✗ No categories found${NC}"
  exit 1
fi
echo

# Test 10: Delete transaction
echo -e "${YELLOW}Test 10: Delete Transaction${NC}"
DELETE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X DELETE "$BASE_URL/transactions/$TRANSACTION_ID" \
  -H "Authorization: Bearer $TOKEN")

if [ "$DELETE_RESPONSE" == "204" ]; then
  echo -e "${GREEN}✓ Transaction deleted successfully${NC}"
else
  echo -e "${RED}✗ Failed to delete transaction (HTTP $DELETE_RESPONSE)${NC}"
  exit 1
fi
echo

# Test 11: Verify deletion
echo -e "${YELLOW}Test 11: Verify Transaction Deletion${NC}"
VERIFY=$(curl -s -X GET "$BASE_URL/transactions/$TRANSACTION_ID" \
  -H "Authorization: Bearer $TOKEN")

ERROR_DETAIL=$(echo $VERIFY | jq -r '.detail')
if [ "$ERROR_DETAIL" == "Transaction not found" ]; then
  echo -e "${GREEN}✓ Transaction successfully deleted (404 returned)${NC}"
else
  echo -e "${RED}✗ Transaction still exists after deletion${NC}"
  exit 1
fi
echo

# Test 12: Invalid token
echo -e "${YELLOW}Test 12: Invalid Token${NC}"
INVALID_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer invalid_token_here")

INVALID_DETAIL=$(echo $INVALID_RESPONSE | jq -r '.detail')
if [ "$INVALID_DETAIL" == "Could not validate credentials" ]; then
  echo -e "${GREEN}✓ Invalid token correctly rejected${NC}"
else
  echo -e "${RED}✗ Invalid token was not rejected${NC}"
  exit 1
fi
echo

echo "========================================"
echo -e "${GREEN}All tests passed successfully! ✓${NC}"
echo "========================================"
