# Docker Deployment Guide

Complete guide to deploying the Telegram Multibot System with Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Compose Services](#docker-compose-services)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Navigate to docker directory
cd docker

# 2. Create environment file
cp ../.env.example ../.env

# 3. Edit .env with your values
nano ../.env

# 4. Start all services
docker compose up -d

# 5. Check status
docker compose ps

# 6. View logs
docker compose logs -f multibot
```

---

## Docker Compose Services

### multibot

The main application container.

| Port | Description |
|------|-------------|
| 8080 | Health check endpoints |
| 8443 | Webhook server (optional) |

### postgres

PostgreSQL 15 database.

| Port | Description |
|------|-------------|
| 5432 | Database (remove in production) |

### redis

Redis for FSM storage (optional but recommended for production).

---

## Configuration

### Environment Variables

Create `.env` in project root:

```bash
# Database
DB_PASSWORD=your_secure_password

# Admin Bot
ADMIN_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ALLOWED_USERS=123456789,987654321

# Your Bots
BOT_SUPPORT_TOKEN=...
BOT_NOTIFICATION_TOKEN=...

# Webhook (optional)
WEBHOOK_ENABLED=false
WEBHOOK_BASE_URL=https://your-domain.com
WEBHOOK_SECRET=your_webhook_secret

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Volume Mounts

| Volume | Purpose |
|--------|---------|
| `../config/bots:/app/config/bots:ro` | Bot configurations |
| `../src/plugins/custom:/app/src/plugins/custom:ro` | Custom plugins |
| `multibot_logs:/app/logs` | Log files |
| `postgres_data:/var/lib/postgresql/data` | Database |
| `redis_data:/data` | Redis persistence |

---

## Production Deployment

### 1. Create Production Override

Create `docker/docker-compose.prod.yml`:

```yaml
services:
  multibot:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M

  postgres:
    restart: always
    ports: []  # Don't expose in production
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

  redis:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

### 2. Deploy

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. With Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/multibot
server {
    listen 443 ssl http2;
    server_name bot.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/bot.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.your-domain.com/privkey.pem;

    # Webhook endpoint
    location /webhook/ {
        proxy_pass http://localhost:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health/ {
        proxy_pass http://localhost:8080;
    }

    # Metrics (restrict access)
    location /metrics {
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://localhost:8080;
    }
}
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

For high availability, run multiple instances behind a load balancer.

**Important**: When using multiple instances:
1. Use Redis for FSM storage (not memory)
2. Use webhook mode (not polling)
3. Configure sticky sessions if needed

```yaml
# docker-compose.scale.yml
services:
  multibot:
    deploy:
      replicas: 3
    environment:
      # Use Redis for FSM
      FSM_STORAGE: redis
      REDIS_URL: redis://redis:6379/0

  nginx:
    image: nginx:alpine
    ports:
      - "8443:8443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - multibot
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multibot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: multibot
  template:
    metadata:
      labels:
        app: multibot
    spec:
      containers:
      - name: multibot
        image: multibot:latest
        ports:
        - containerPort: 8080
        - containerPort: 8443
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: multibot-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "250m"
            memory: "256Mi"
```

---

## Monitoring

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health/live` | Liveness probe |
| `/health/ready` | Readiness probe |
| `/health/full` | Detailed status |
| `/metrics` | Prometheus metrics |

### Prometheus Integration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'multibot'
    static_configs:
      - targets: ['multibot:8080']
    metrics_path: /metrics
```

### Grafana Dashboard

Available metrics:

- `multibot_bots_total` - Total bots configured
- `multibot_bots_running` - Running bots count
- `multibot_bot_running{bot_id="..."}` - Bot status (0/1)
- `multibot_bot_uptime_seconds{bot_id="..."}` - Bot uptime
- `multibot_db_pool_size` - Database pool size
- `multibot_db_pool_free` - Free database connections

### Log Aggregation

Logs are JSON formatted for easy parsing:

```bash
# View structured logs
docker compose logs -f multibot | jq .

# Filter by log level
docker compose logs -f multibot | jq 'select(.level == "ERROR")'

# Filter by bot
docker compose logs -f multibot | jq 'select(.bot_id == "support_bot")'
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs multibot

# Check if dependencies are healthy
docker compose ps

# Rebuild image
docker compose build --no-cache multibot
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connectivity
docker compose exec multibot python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('$DATABASE_URL')
    print(await conn.fetchval('SELECT 1'))
    await conn.close()
asyncio.run(test())
"
```

### Migrations Not Applied

```bash
# Run migrations manually
docker compose exec multibot sh -c "cd /app && alembic upgrade head"

# Check migration status
docker compose exec multibot sh -c "cd /app && alembic current"
```

### Health Check Failing

```bash
# Check health endpoint directly
curl http://localhost:8080/health/live
curl http://localhost:8080/health/ready

# Check detailed status
curl http://localhost:8080/health/full | jq .
```

### Hot Reload Not Working

```bash
# Check if volumes are mounted correctly
docker compose exec multibot ls -la /app/config/bots/

# Check watcher logs
docker compose logs -f multibot | grep -i watcher
```

### Memory Issues

```bash
# Check memory usage
docker stats multibot

# Increase memory limit in docker-compose
deploy:
  resources:
    limits:
      memory: 2G
```

---

## Backup & Restore

### Database Backup

```bash
# Backup
docker compose exec postgres pg_dump -U multibot multibot > backup.sql

# Restore
docker compose exec -T postgres psql -U multibot multibot < backup.sql
```

### Configuration Backup

```bash
# Backup configs
tar -czf config-backup.tar.gz config/bots/ .env

# Backup custom plugins
tar -czf plugins-backup.tar.gz src/plugins/custom/
```

---

## Security Checklist

- [ ] Use strong database password
- [ ] Don't expose PostgreSQL port in production
- [ ] Set `WEBHOOK_SECRET` for webhook mode
- [ ] Restrict `/metrics` endpoint access
- [ ] Run container as non-root user (already configured)
- [ ] Use secrets management for tokens
- [ ] Enable SSL/TLS for webhooks
- [ ] Keep images updated
