# Deployment Guide

Complete guide for deploying Personal Finance Tracker to production.

## Prerequisites

- Docker and Docker Compose installed
- GitHub account with repository access
- Docker Hub account (or other container registry)
- Server with Docker support (VPS, AWS EC2, DigitalOcean, etc.)
- Domain name (optional, but recommended)

## Environment Variables

### Required Production Variables

Create a `.env` file on your production server with these variables:

```bash
# Application
APP_NAME=Personal Finance Tracker
DEBUG=False
ALLOWED_ORIGINS=["https://your-domain.com"]

# Database
DATABASE_URL=postgresql+asyncpg://postgres:STRONG_PASSWORD@postgres:5432/finance_tracker

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# JWT Authentication - MUST BE CHANGED!
SECRET_KEY=generate-strong-random-key-here-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# OCR Configuration
OCR_LANGUAGE=en
USE_PADDLEOCR=True
USE_TESSERACT=True

# Currency
DEFAULT_CURRENCY=USD
EXCHANGE_RATE_API_URL=https://api.exchangerate.host/latest

# Sentry Monitoring (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Generate Secure SECRET_KEY

```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## CI/CD with GitHub Actions

### Setup GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

1. **DOCKER_USERNAME** - Your Docker Hub username
2. **DOCKER_PASSWORD** - Your Docker Hub password or access token

### CI/CD Pipeline

The pipeline automatically runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

Pipeline stages:

1. **Test** - Runs pytest with PostgreSQL and Redis services
2. **Lint** - Runs Black, Ruff, and MyPy checks
3. **Build** - Builds Docker image
4. **Deploy** - Pushes image to Docker Hub (main branch only)

To trigger deployment:
```bash
git push origin main
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Small-Medium Scale)

1. **Clone repository on server:**
```bash
git clone https://github.com/yourusername/personal-finance-tracker.git
cd personal-finance-tracker/Personal-Finance-Tracking
```

2. **Create production .env file:**
```bash
cp .env.example .env
nano .env  # Edit with production values
```

3. **Start services:**
```bash
docker-compose up -d
```

4. **Apply database migrations:**
```bash
docker-compose exec api alembic upgrade head
```

5. **Verify deployment:**
```bash
docker-compose ps
curl http://localhost:8000/health
```

### Option 2: Using Pre-built Docker Image

1. **Pull image from Docker Hub:**
```bash
docker pull yourusername/finance-tracker:latest
```

2. **Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: finance_tracker
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    image: yourusername/finance-tracker:latest
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads

  celery:
    image: yourusername/finance-tracker:latest
    command: celery -A app.tasks.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads

volumes:
  postgres_data:
```

3. **Start services:**
```bash
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Option 3: Kubernetes Deployment

For Kubernetes deployment, see `docs/kubernetes/` directory for manifests (TODO).

## Reverse Proxy Setup (Nginx)

### Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### Configure Nginx

Create `/etc/nginx/sites-available/finance-tracker`:

```nginx
upstream finance_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://finance_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://finance_api/health;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/finance-tracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring with Sentry

### Setup Sentry

1. Create account at [sentry.io](https://sentry.io)
2. Create new project (Python/FastAPI)
3. Copy DSN from project settings
4. Add to `.env`:
```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
```

5. Restart services:
```bash
docker-compose restart api celery
```

Sentry will automatically capture:
- Unhandled exceptions
- API errors
- Performance metrics
- Database query performance

## Health Checks

Verify deployment health:

```bash
# API health
curl https://your-domain.com/health

# API version
curl https://your-domain.com/version

# Docker services
docker-compose ps

# API logs
docker-compose logs -f api

# Celery logs
docker-compose logs -f celery

# Database connection
docker-compose exec postgres psql -U postgres -d finance_tracker -c "SELECT COUNT(*) FROM users;"
```

## Backup Strategy

### Database Backups

Create backup script `/usr/local/bin/backup-finance-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/finance-tracker"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U postgres finance_tracker | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Make executable and add to cron:
```bash
chmod +x /usr/local/bin/backup-finance-db.sh
crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-finance-db.sh
```

### Upload Directory Backups

```bash
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

## Scaling Considerations

### Horizontal Scaling

To scale API instances:
```bash
docker-compose up -d --scale api=3
```

Add load balancer (Nginx):
```nginx
upstream finance_api {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}
```

### Database Scaling

For production traffic:
- Enable PostgreSQL connection pooling (PgBouncer)
- Configure read replicas
- Consider managed database (AWS RDS, DigitalOcean Managed DB)

### Redis Scaling

For high availability:
- Use Redis Sentinel for failover
- Consider Redis Cluster for data sharding
- Or use managed Redis (AWS ElastiCache, Redis Cloud)

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall (UFW/iptables)
- [ ] Disable DEBUG mode in production
- [ ] Set restrictive ALLOWED_ORIGINS
- [ ] Regular security updates: `docker-compose pull && docker-compose up -d`
- [ ] Enable Sentry for error tracking
- [ ] Configure backup automation
- [ ] Review and rotate JWT tokens periodically
- [ ] Implement rate limiting (TODO: add middleware)
- [ ] Setup monitoring and alerting

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - Database not ready: Wait for health check
# - Environment variables: Verify .env file
# - Port conflict: Check if 8000 is in use
```

### Database migration errors

```bash
# Check current migration
docker-compose exec api alembic current

# Force migration
docker-compose exec api alembic upgrade head

# Rollback if needed
docker-compose exec api alembic downgrade -1
```

### Celery tasks not processing

```bash
# Check Celery logs
docker-compose logs celery

# Verify Redis connection
docker-compose exec redis redis-cli ping

# Restart Celery
docker-compose restart celery
```

### High memory usage

```bash
# Check resource usage
docker stats

# Limit container resources in docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Apply migrations
docker-compose exec api alembic upgrade head
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U postgres -d finance_tracker -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U postgres -d finance_tracker -c "SELECT pg_size_pretty(pg_database_size('finance_tracker'));"
```

### Log Rotation

Configure Docker log rotation in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/personal-finance-tracker/issues
- Documentation: https://github.com/yourusername/personal-finance-tracker/docs

## Additional Resources

- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Celery Production Guide](https://docs.celeryproject.org/en/stable/userguide/deployment.html)
