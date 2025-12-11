#!/bin/bash

# Quick Receipt Upload Script

if [ $# -eq 0 ]; then
    echo "Usage: ./upload_receipt.sh <path_to_receipt_file>"
    echo "Example: ./upload_receipt.sh receipt.pdf"
    exit 1
fi

RECEIPT_FILE="$1"

if [ ! -f "$RECEIPT_FILE" ]; then
    echo "Error: File '$RECEIPT_FILE' not found!"
    exit 1
fi

BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="testpassword123"

echo "🔐 Logging in..."
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" \
  | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Login failed! Check your credentials."
    exit 1
fi

echo "✅ Login successful"
echo ""

echo "📤 Uploading: $RECEIPT_FILE"
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/uploads" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$RECEIPT_FILE")

DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.id')
STATUS=$(echo $UPLOAD_RESPONSE | jq -r '.status')

if [ "$DOCUMENT_ID" == "null" ]; then
    echo "❌ Upload failed!"
    echo $UPLOAD_RESPONSE | jq .
    exit 1
fi

echo "✅ Upload successful!"
echo "   Document ID: $DOCUMENT_ID"
echo "   Status: $STATUS"
echo ""

echo "⏳ Processing (waiting 15 seconds)..."
for i in {15..1}; do
    echo -n "$i... "
    sleep 1
done
echo ""
echo ""

echo "📊 Checking results..."
RESULT=$(curl -s -X GET "$BASE_URL/uploads/$DOCUMENT_ID" \
  -H "Authorization: Bearer $TOKEN")

FINAL_STATUS=$(echo $RESULT | jq -r '.status')
RAW_TEXT=$(echo $RESULT | jq -r '.raw_text')
EXTRACTED_DATA=$(echo $RESULT | jq -r '.extracted_data')

echo "Status: $FINAL_STATUS"
echo ""

if [ "$FINAL_STATUS" == "processed" ]; then
    echo "✅ Processing complete!"
    echo ""
    echo "📝 Extracted Text:"
    echo "$RAW_TEXT" | head -10
    echo ""
    echo "💰 Parsed Data:"
    echo "$EXTRACTED_DATA" | jq .
    echo ""

    # Check for created transaction
    echo "🔍 Checking for auto-created transaction..."
    TRANSACTIONS=$(curl -s -X GET "$BASE_URL/transactions?limit=5" \
      -H "Authorization: Bearer $TOKEN")

    TRANSACTION=$(echo $TRANSACTIONS | jq ".[] | select(.document_id == $DOCUMENT_ID)")

    if [ -n "$TRANSACTION" ] && [ "$TRANSACTION" != "null" ]; then
        echo "✅ Transaction created!"
        echo $TRANSACTION | jq '{id, date, amount, merchant, category_id}'
    else
        echo "⚠️  No transaction created (amount or date may not have been detected)"
    fi
elif [ "$FINAL_STATUS" == "failed" ]; then
    ERROR_MSG=$(echo $RESULT | jq -r '.error_message')
    echo "❌ Processing failed: $ERROR_MSG"
elif [ "$FINAL_STATUS" == "processing" ] || [ "$FINAL_STATUS" == "queued" ]; then
    echo "⏳ Still processing... Check status later with:"
    echo "   curl -X GET $BASE_URL/uploads/$DOCUMENT_ID -H \"Authorization: Bearer \$TOKEN\""
fi

echo ""
echo "📋 View all your transactions:"
echo "   http://localhost:8000/docs#/transactions/list_transactions_transactions_get"
