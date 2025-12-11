# Docker Installation Guide for macOS (Apple Silicon)

Ваша система: **macOS 15.6.1 (Sequoia), Apple Silicon (ARM64)**

## Способ 1: Docker Desktop (Рекомендуется)

### Шаг 1: Скачивание

**Откройте браузер и перейдите по ссылке:**

🔗 https://desktop.docker.com/mac/main/arm64/Docker.dmg

**Или посетите официальный сайт:**
https://www.docker.com/products/docker-desktop

### Шаг 2: Установка

1. Откройте скачанный файл `Docker.dmg`
2. Перетащите Docker.app в папку Applications
3. Откройте Docker из папки Applications
4. При первом запуске:
   - Разрешите Docker необходимые права доступа
   - Дождитесь запуска Docker Engine (значок кита в строке меню)
   - Примите условия использования (Terms of Service)

### Шаг 3: Проверка установки

Откройте Terminal и выполните:

```bash
docker --version
docker compose version
```

Вы должны увидеть версии Docker (например, Docker version 24.x.x).

### Шаг 4: Проверка работы

```bash
# Запустить тестовый контейнер
docker run hello-world
```

Если вы видите сообщение "Hello from Docker!", установка прошла успешно! ✅

## Способ 2: Homebrew (альтернатива)

```bash
# Установить Homebrew (если ещё не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установить Docker Desktop через Homebrew
brew install --cask docker

# Запустить Docker Desktop
open /Applications/Docker.app
```

## Запуск проекта после установки Docker

```bash
# Перейти в папку проекта
cd /Users/viktorkabelkov/PycharmProjects/personal-finance-tracker

# Создать .env файл (если ещё не создан)
cp .env.example .env

# Запустить все сервисы
docker compose up -d

# Применить миграции БД
docker compose exec app alembic upgrade head

# Проверить статус
docker compose ps

# Посмотреть логи
docker compose logs -f
```

## Проверка работы API

После запуска откройте в браузере:

- **API Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Полезные команды Docker

```bash
# Просмотр запущенных контейнеров
docker ps

# Просмотр всех контейнеров
docker ps -a

# Остановить все сервисы
docker compose stop

# Перезапустить сервисы
docker compose restart

# Удалить контейнеры и volumes
docker compose down -v

# Просмотр логов конкретного сервиса
docker compose logs -f app
docker compose logs -f postgres
docker compose logs -f celery_worker

# Войти в контейнер
docker compose exec app bash
docker compose exec postgres psql -U postgres -d finance_tracker

# Применить миграции
docker compose exec app alembic upgrade head

# Создать новую миграцию
docker compose exec app alembic revision --autogenerate -m "Description"

# Запустить тесты
docker compose exec app pytest

# Пересобрать образы после изменения кода
docker compose build
docker compose up -d
```

## Настройка Docker Desktop

### Рекомендуемые настройки:

1. **Resources** (Ресурсы):
   - CPUs: 4-6 (зависит от вашего Mac)
   - Memory: 8 GB
   - Swap: 2 GB
   - Disk image size: 64 GB

2. **General**:
   - ✅ Start Docker Desktop when you log in
   - ✅ Use Virtualization framework
   - ✅ Enable VirtioFS

3. **Docker Engine**:
   Оставьте настройки по умолчанию

## Troubleshooting

### Проблема: Docker Desktop не запускается

```bash
# Перезапустить Docker
killall Docker && open /Applications/Docker.app

# Или через терминал
pkill -SIGHUP -f /Applications/Docker.app
open /Applications/Docker.app
```

### Проблема: "Cannot connect to Docker daemon"

```bash
# Убедитесь, что Docker Desktop запущен
# Значок кита должен быть в строке меню

# Проверьте контекст
docker context ls
docker context use desktop-linux
```

### Проблема: Контейнеры не запускаются

```bash
# Просмотр логов
docker compose logs

# Удалить старые контейнеры и volumes
docker compose down -v

# Пересобрать образы
docker compose build --no-cache

# Запустить заново
docker compose up -d
```

### Проблема: Порт 8000 уже занят

```bash
# Найти процесс на порту 8000
lsof -i :8000

# Убить процесс (замените PID на номер процесса)
kill -9 PID

# Или измените порт в docker-compose.yml:
# - "8001:8000"  # Доступ через http://localhost:8001
```

### Проблема: Нет места на диске

```bash
# Очистить неиспользуемые образы
docker image prune -a

# Очистить неиспользуемые volumes
docker volume prune

# Очистить всё неиспользуемое
docker system prune -a --volumes
```

## Альтернатива: Colima (лёгкая альтернатива Docker Desktop)

Если Docker Desktop работает медленно:

```bash
# Установить через Homebrew
brew install colima docker docker-compose

# Запустить Colima
colima start --cpu 4 --memory 8 --arch aarch64

# Проверить
docker ps

# Использовать как обычно
cd /Users/viktorkabelkov/PycharmProjects/personal-finance-tracker
docker compose up -d
```

## Следующие шаги после установки

1. ✅ Установить Docker Desktop
2. ✅ Проверить командой `docker --version`
3. ✅ Запустить проект: `docker compose up -d`
4. ✅ Открыть http://localhost:8000/docs
5. ✅ Начать использование API!

## Полезные ссылки

- **Docker Desktop для Mac**: https://docs.docker.com/desktop/install/mac-install/
- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **Colima**: https://github.com/abiosoft/colima

---

Если у вас возникли проблемы, сообщите об ошибке, которую вы видите! 🚀
