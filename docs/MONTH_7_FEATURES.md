# Month 7: Advanced Features

Complete documentation for WebSocket, Export, and Telegram Bot features.

## 🔌 WebSocket Real-time Updates

### Overview

WebSocket endpoint provides real-time updates for document processing and transaction events.

### Connection

```javascript
const token = "YOUR_JWT_TOKEN";
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
  console.log("Connected to WebSocket");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from WebSocket");
};
```

### Event Types

**Connection Events:**
```json
{
  "type": "connection_established",
  "data": {
    "user_id": 123,
    "email": "user@example.com"
  }
}
```

**Document Processing Events:**
```json
{
  "type": "document_processing_started",
  "data": {
    "document_id": 456,
    "status": "started"
  },
  "timestamp": 1234567890.123
}

{
  "type": "document_processing_progress",
  "data": {
    "document_id": 456,
    "status": "progress",
    "progress": 50
  },
  "timestamp": 1234567891.123
}

{
  "type": "document_processing_completed",
  "data": {
    "document_id": 456,
    "status": "completed"
  },
  "timestamp": 1234567892.123
}

{
  "type": "document_processing_failed",
  "data": {
    "document_id": 456,
    "status": "failed",
    "error": "OCR failed: Invalid image format"
  },
  "timestamp": 1234567893.123
}
```

**Transaction Events:**
```json
{
  "type": "transaction_created",
  "data": {
    "id": 789,
    "amount": 50.00,
    "description": "Grocery shopping",
    "date": "2024-01-15"
  }
}

{
  "type": "transaction_updated",
  "data": {
    "id": 789,
    "amount": 55.00
  }
}

{
  "type": "transaction_deleted",
  "data": {
    "id": 789
  }
}
```

### Keep-Alive (Ping/Pong)

Send ping to keep connection alive:
```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  }
}, 30000); // Every 30 seconds
```

### React Example

```jsx
import { useEffect, useState } from 'react';

function useWebSocket(token) {
  const [ws, setWs] = useState(null);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const websocket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);

      // Handle specific events
      if (message.type === 'document_processing_completed') {
        console.log('Document processed:', message.data.document_id);
        // Refresh document list or show notification
      }
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [token]);

  return { ws, messages };
}

// Usage
function App() {
  const { messages } = useWebSocket(localStorage.getItem('token'));

  return (
    <div>
      <h1>Real-time Updates</h1>
      {messages.map((msg, i) => (
        <div key={i}>{msg.type}: {JSON.stringify(msg.data)}</div>
      ))}
    </div>
  );
}
```

---

## 📊 Export Functionality

### CSV Export

**Endpoint:** `GET /export/transactions/csv`

**Parameters:**
- `start_date` (optional): Filter start date (YYYY-MM-DD)
- `end_date` (optional): Filter end date (YYYY-MM-DD)
- `category_id` (optional): Filter by category

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/export/transactions/csv?start_date=2024-01-01&end_date=2024-01-31" \
  -o transactions.csv
```

**CSV Format:**
```csv
ID,Date,Description,Amount,Currency,Type,Category,Merchant,Notes,Created At
1,2024-01-15,Grocery shopping,50.00,USD,expense,Food,Walmart,,2024-01-15 10:30:00
2,2024-01-14,Salary,2000.00,USD,income,Income,Company Inc,,2024-01-14 09:00:00
```

### Excel Export (Transactions)

**Endpoint:** `GET /export/transactions/excel`

**Parameters:** Same as CSV

**Features:**
- Multiple sheets:
  - **Transactions**: Complete transaction list
  - **Summary**: Key statistics
  - **By Category**: Category breakdown

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/export/transactions/excel" \
  -o transactions.xlsx
```

### Excel Export (Analytics)

**Endpoint:** `GET /export/analytics/excel`

**Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Sheets:**
- **Monthly Trends**: Income/expense by month
- **Category Breakdown**: Spending by category
- **Top Merchants**: Top 10 merchants by spending

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/export/analytics/excel?start_date=2024-01-01" \
  -o analytics.xlsx
```

### Python Client Example

```python
import requests

token = "YOUR_JWT_TOKEN"
headers = {"Authorization": f"Bearer {token}"}

# Export to CSV
response = requests.get(
    "http://localhost:8000/export/transactions/csv",
    headers=headers,
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
)

with open("transactions.csv", "wb") as f:
    f.write(response.content)

# Export to Excel
response = requests.get(
    "http://localhost:8000/export/transactions/excel",
    headers=headers
)

with open("transactions.xlsx", "wb") as f:
    f.write(response.content)
```

### JavaScript/Fetch Example

```javascript
async function exportTransactions(format = 'csv') {
  const token = localStorage.getItem('token');
  const endpoint = format === 'csv'
    ? '/export/transactions/csv'
    : '/export/transactions/excel';

  const response = await fetch(`http://localhost:8000${endpoint}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transactions.${format === 'csv' ? 'csv' : 'xlsx'}`;
  a.click();
}

// Usage
exportTransactions('csv');
exportTransactions('excel');
```

---

## 🤖 Telegram Bot Integration

### Setup

1. **Create Bot:**
   - Open Telegram and search for [@BotFather](https://t.me/Botfather)
   - Send `/newbot` and follow instructions
   - Copy the token

2. **Configure:**
   ```bash
   # In .env file
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

3. **Start Bot:**
   ```bash
   python scripts/run_telegram_bot.py
   ```

### Commands

#### Authentication
```
/start - Initialize bot and see available commands
/auth YOUR_JWT_TOKEN - Link your Finance Tracker account
/help - Show help message
```

**Example:**
```
/auth eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
✅ Authentication successful!
```

#### Add Transactions
```
/expense [amount] [description] - Add expense
/income [amount] [description] - Add income
```

**Examples:**
```
/expense 50 Grocery shopping at Walmart
✅ Expense added!
💸 Amount: $50
📝 Description: Grocery shopping at Walmart
📅 Date: 2024-01-15

/income 1000 Freelance payment
✅ Income added!
💵 Amount: $1000
📝 Description: Freelance payment
```

#### View Data
```
/summary - View financial summary
/month - Current month statistics
/recent - Last 10 transactions
/export - Export transactions
```

**Example:**
```
/summary

📊 Financial Summary

💵 Income: $5,240.00
💸 Expenses: $3,180.50
💰 Balance: $2,059.50

📈 This Month:
  Income: $1,200.00
  Expenses: $845.30
  Net: +$354.70
```

### Button Interface

The bot provides convenient buttons:
- 💰 Add Expense
- 💵 Add Income
- 📊 Summary
- 📈 This Month
- 📋 Recent Transactions
- ⚙️ Settings

### Integration with API

To integrate bot with the actual API (currently shows mock data):

1. **Add API client to bot:**
```python
# In app/telegram_bot/bot.py

import httpx
from app.core.config import settings

async def create_transaction(user_token: str, data: dict):
    """Create transaction via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.API_URL}/transactions",
            json=data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        return response.json()
```

2. **Update command handlers:**
```python
async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first")
        return

    token = user_sessions[user_id]["jwt_token"]
    amount = Decimal(context.args[0])
    description = " ".join(context.args[1:])

    # Create transaction via API
    transaction = await create_transaction(token, {
        "amount": float(amount),
        "description": description,
        "transaction_type": "expense",
        "date": date.today().isoformat()
    })

    await update.message.reply_text(
        f"✅ Expense added!\n"
        f"ID: {transaction['id']}\n"
        f"Amount: ${amount}"
    )
```

### Production Deployment

**Option 1: Polling (Recommended for testing)**
```bash
python scripts/run_telegram_bot.py
```

**Option 2: Webhook (Recommended for production)**

1. Set webhook URL in .env:
```bash
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook
```

2. Add webhook endpoint to FastAPI:
```python
# app/api/telegram_webhook.py
from fastapi import APIRouter, Request
from app.telegram_bot import application

router = APIRouter(prefix="/telegram")

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook."""
    update = await request.json()
    await application.process_update(update)
    return {"status": "ok"}
```

3. Set webhook:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/telegram/webhook"
```

### Docker Integration

Add to docker-compose.yml:
```yaml
telegram-bot:
  build: .
  command: python scripts/run_telegram_bot.py
  depends_on:
    - postgres
    - redis
  env_file:
    - .env
  volumes:
    - ./uploads:/app/uploads
```

---

## Testing

### WebSocket Testing

```bash
# Using wscat
npm install -g wscat
wscat -c "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"

# Send ping
> {"type": "ping"}
< {"type": "pong"}
```

### Export Testing

```bash
# Test CSV export
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/export/transactions/csv" | head

# Test Excel export
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/export/transactions/excel" -o test.xlsx
```

### Telegram Bot Testing

1. Start bot: `python scripts/run_telegram_bot.py`
2. Open Telegram and search for your bot
3. Send `/start`
4. Authenticate with `/auth YOUR_TOKEN`
5. Test commands

---

## Troubleshooting

### WebSocket Issues

**Problem:** Connection refused
```
Solution: Ensure server is running with WebSocket support
uvicorn app.main:app --reload --ws-max-size 16777216
```

**Problem:** Authentication failed
```
Solution: Check JWT token is valid and not expired
```

### Export Issues

**Problem:** No data found
```
Solution: Ensure you have transactions and correct date filters
```

**Problem:** Excel formatting issues
```
Solution: Install openpyxl and xlsxwriter:
pip install openpyxl xlsxwriter
```

### Telegram Bot Issues

**Problem:** Bot not responding
```
Solution: Check TELEGRAM_BOT_TOKEN in .env
Check bot is running: python scripts/run_telegram_bot.py
```

**Problem:** Commands not working
```
Solution: Send /start to initialize bot
Authenticate with /auth YOUR_TOKEN
```

---

## Next Steps

- Integrate WebSocket notifications in document processing
- Add real API calls to Telegram bot
- Implement scheduled reports via Telegram
- Add webhook mode for production Telegram bot
- Create frontend components for WebSocket integration
- Add export scheduling (daily/weekly reports)
