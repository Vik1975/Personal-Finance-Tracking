# Personal Finance Tracker

API service for automatic expense tracking based on documents (receipts, invoices, bills) with OCR, categorization, and analytics.

## Features

- **Document Upload**: Accept PDF, JPG, PNG files (receipts, invoices, bills)
- **OCR and Parsing**: Extract structured data (PaddleOCR, Tesseract, PyMuPDF, pdfplumber)
- **Auto-categorization**: Automatic transaction classification based on rules and ML
- **Financial Management**: Accounts, budgets, transactions, categories
- **Analytics**: Reports, charts, KPIs, filters by periods and categories
- **Security**: JWT authentication, roles (user/admin)
- **Async/Background**: Asynchronous processing via Celery

## Technology Stack

- **Backend**: FastAPI + Uvicorn (ASGI)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async) + Alembic
- **Queue**: Redis + Celery 5.6
- **OCR**: PaddleOCR, Tesseract, PyMuPDF, pdfplumber
- **Auth**: JWT (python-jose, passlib)
- **HTTP Client**: httpx (async)
- **Monitoring**: Sentry SDK
- **Testing**: pytest + pytest-asyncio
- **DevOps**: Docker, docker-compose, GitHub Actions

## Architecture

```
personal-finance-tracker/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Configuration, security
│   ├── db/               # SQLAlchemy models, sessions
│   ├── processing/       # OCR, document parsing
│   └── tasks/            # Celery tasks
├── alembic/              # Database migrations
├── tests/                # Tests
├── docker-compose.yml    # Services orchestration
├── Dockerfile            # Application container
└── requirements.txt      # Python dependencies
```

## Quick Start

### 1. Clone and Setup

```bash
cd personal-finance-tracker
cp .env.example .env
# Edit .env if necessary
```

### 2. Launch via Docker Compose

```bash
docker-compose up -d
```

Services:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 3. Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Apply migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# In separate terminal: Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Optional: Start Telegram bot
python scripts/run_telegram_bot.py
```

## Database

### Initialize Alembic

```bash
# Alembic is already configured, but if you need to recreate:
alembic init alembic
```

### Create Migration

```bash
# Auto-generate migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Data Models

- **users**: Users
- **accounts**: Accounts/wallets (cards, cash, bank)
- **categories**: Tree of expense/income categories
- **documents**: Uploaded documents
- **transactions**: Financial transactions
- **line_items**: Items from receipts/bills
- **budgets**: Budget limits
- **rules**: Auto-categorization rules

## API Endpoints

### Basic

- `GET /` - Service information
- `GET /health` - Health check
- `GET /version` - API version

### Authentication ✅

- `POST /auth/signup` - Registration
- `POST /auth/login` - Login (get JWT)
- `GET /auth/me` - User profile

### Documents ✅

- `POST /uploads` - Upload document
- `GET /documents/{id}` - Status and metadata
- `POST /documents/{id}/process` - Start processing

### Transactions ✅

- `GET /transactions` - List with filters
- `POST /transactions` - Create manually
- `PUT /transactions/{id}` - Update
- `DELETE /transactions/{id}` - Delete

### Analytics ✅

- `GET /analytics/summary` - Total amounts, top categories
- `GET /analytics/trends` - Data for charts

### Budgets ✅

- `GET /budgets` - List of budgets
- `POST /budgets` - Create budget

### Export ✅

- `GET /export/transactions/csv` - Export transactions to CSV
- `GET /export/transactions/excel` - Export to Excel with multiple sheets
- `GET /export/analytics/excel` - Export analytics report

### WebSocket ✅

- `WS /ws?token=JWT` - Real-time updates for document processing and transactions

### Telegram Bot ✅

- `/start` - Initialize bot
- `/auth [token]` - Link account
- `/expense [amount] [description]` - Add expense
- `/income [amount] [description]` - Add income
- `/summary` - View summary
- `/recent` - Recent transactions
- `/export` - Export data

## Document Processing Pipeline

1. **Upload**: Receive file → save → record in DB
2. **Queue**: Add task to Celery
3. **OCR/Parse**:
   - PDF: PyMuPDF/pdfplumber (text/tables) → fallback OCR
   - Images: PaddleOCR → field extraction
4. **Normalize**: Dates, currencies, amounts
5. **Categorize**: Rules + ML model
6. **Save**: Transactions + line_items to DB

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_transactions.py
```

## Linting and Formatting

```bash
# Black (formatting)
black app/ tests/

# Ruff (linter)
ruff check app/ tests/

# MyPy (type checking)
mypy app/
```

## CI/CD

GitHub Actions can be configured for:
- Docker image build
- Running tests
- Image publication (on push to main)

See `.github/workflows/ci.yml` (TODO: Configure in Month 6)

## Monitoring and Observability

### Sentry

```python
# In .env
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
```

Integration automatically captures:
- Unhandled exceptions
- Performance traces
- HTTP requests

## Roadmap

### ✅ Month 1: Foundation (Steps A-B)
- [x] Project structure
- [x] FastAPI framework
- [x] Docker/docker-compose
- [x] SQLAlchemy 2.0 models
- [x] Alembic migrations

### ✅ Month 2: Auth & Upload (Steps C-D)
- [x] JWT authentication
- [x] Endpoint protection
- [x] File upload
- [x] Celery tasks

### ✅ Month 3: OCR (Step E)
- [x] PaddleOCR integration
- [x] PDF parsing (PyMuPDF/pdfplumber)
- [x] Receipt data extraction
- [x] Normalization

### ✅ Month 4: Finance (Step F)
- [x] Categories and rules
- [x] Budgets
- [x] Analytics and reports
- [x] Charts

### ✅ Month 5: Quality (Step G)
- [x] Tests (100 passing tests)
- [x] Load tests
- [x] Integration tests
- [x] Unit tests for all modules

### ✅ Month 6: Prod (Steps H-I)
- [x] CI/CD (GitHub Actions)
- [x] Deployment configuration
- [x] Sentry integration
- [x] Documentation

### ✅ Month 7: Advanced Features (Step J)
- [x] WebSocket for realtime status updates
- [x] Export to CSV/Excel
- [x] Telegram bot integration

## Future Features

- LayoutParser for complex layouts
- ML categorization model
- Multi-currency support with exchange rates
- Recurring payments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push and create a Pull Request

## License

MIT

## Contact

Questions and suggestions: [GitHub Issues](https://github.com/yourusername/personal-finance-tracker/issues)
