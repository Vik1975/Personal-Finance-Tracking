# Quick Start Guide

## Вариант 1: С Docker (Рекомендуется)

Требуется установленный Docker и Docker Compose.

```bash
# 1. Создать .env файл
cp .env.example .env

# 2. Запустить все сервисы
docker compose up -d

# 3. Применить миграции БД
docker compose exec app alembic upgrade head

# 4. Проверить работу
curl http://localhost:8000/health
```

**Сервисы:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Остановка:**
```bash
docker compose down
```

## Вариант 2: Локально (без Docker)

### Шаг 1: Установка зависимостей

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### Шаг 2: Запуск БД (PostgreSQL и Redis)

**Вариант A: Docker для БД**
```bash
# PostgreSQL
docker run -d --name finance-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=finance_tracker \
  -p 5432:5432 \
  postgres:15-alpine

# Redis
docker run -d --name finance-redis \
  -p 6379:6379 \
  redis:7-alpine
```

**Вариант B: SQLite (упрощённый режим)**
```bash
# Отредактировать .env:
DATABASE_URL=sqlite+aiosqlite:///./finance_tracker.db
```

### Шаг 3: Миграции БД

```bash
# Применить миграции
alembic upgrade head
```

### Шаг 4: Запуск приложения

```bash
# Запустить API сервер
uvicorn app.main:app --reload

# В отдельном терминале: Celery worker (опционально)
celery -A app.tasks.celery_app worker --loglevel=info
```

**Или используйте скрипт:**
```bash
./start.sh
```

## Быстрый тест

```bash
# 1. Проверка работы
curl http://localhost:8000/health

# 2. Регистрация пользователя
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "testpass123"
  }'

# 3. Вход
curl -X POST http://localhost:8000/auth/login \
  -d "username=test@example.com&password=testpass123"

# Сохраните токен из ответа
TOKEN="your_access_token_here"

# 4. Получить профиль
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 5. Список категорий
curl http://localhost:8000/categories/all \
  -H "Authorization: Bearer $TOKEN"

# 6. Создать счёт
curl -X POST http://localhost:8000/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Card",
    "account_type": "card",
    "currency": "USD",
    "balance": 1000.00
  }'

# 7. Создать транзакцию
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-01-10",
    "amount": 25.50,
    "currency": "USD",
    "merchant": "Starbucks",
    "is_expense": true
  }'

# 8. Аналитика
curl "http://localhost:8000/analytics/summary?date_from=2025-01-01" \
  -H "Authorization: Bearer $TOKEN"
```

## Swagger UI

Откройте браузер: http://localhost:8000/docs

Здесь вы можете:
- Просмотреть все API endpoints
- Тестировать запросы интерактивно
- Авторизоваться (кнопка "Authorize")

## Troubleshooting

### Ошибка: "Cannot connect to database"
- Проверьте, что PostgreSQL запущен: `docker ps` или `psql -V`
- Проверьте DATABASE_URL в .env файле

### Ошибка: "Cannot connect to Redis"
- Проверьте, что Redis запущен: `docker ps` или `redis-cli ping`
- Проверьте REDIS_URL в .env файле

### Ошибка: "ModuleNotFoundError"
- Активируйте виртуальное окружение: `source venv/bin/activate`
- Переустановите зависимости: `pip install -r requirements.txt`

### OCR не работает
- Установите Tesseract:
  - Mac: `brew install tesseract`
  - Ubuntu: `sudo apt-get install tesseract-ocr`
- PaddleOCR установится автоматически с зависимостями

## Полезные команды

```bash
# Просмотр логов (Docker)
docker compose logs -f app

# Остановка сервисов
docker compose stop

# Перезапуск
docker compose restart

# Удаление всех данных
docker compose down -v

# Применить новые миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Запуск тестов
pytest

# Форматирование кода
black app/ tests/

# Проверка кода
ruff check app/ tests/
```

## Следующие шаги

1. Изучите API документацию: http://localhost:8000/docs
2. Создайте несколько тестовых транзакций
3. Загрузите тестовый чек (PDF или JPG)
4. Настройте правила категоризации
5. Создайте бюджеты и отслеживайте расходы

Удачи! 🚀
