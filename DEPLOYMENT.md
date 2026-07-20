# AstroSage AI — Deployment Guide

## Quick Start (Development)

```bash
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-
docker compose up --build

# Or without Docker:
make dev
```

## Production Deployment

### Prerequisites

- Docker & Docker Compose on the target host
- Domain name with DNS pointing to the server
- 4GB+ RAM recommended (2GB minimum)
- SSL certificate (Let's Encrypt recommended)

### 1. Server Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Clone
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-
```

### 2. Configure Environment

```bash
cp .env.production .env

# Generate a secure secret key
openssl rand -hex 32

# Edit .env with your values:
# - SECRET_KEY (the generated key above)
# - POSTGRES_PASSWORD (a strong password)
# - CORS_ORIGINS (your domain)
nano .env
```

### 3. Knowledge Base

The knowledge base (v1.0.0 frozen release) contains 120K chunks, 391 entities, and 5044 relationships.

```bash
# The Dockerfile copies the knowledge base into the image.
# Alternatively, mount it as a volume in production:
#   -v /path/to/knowledge:/app/knowledge/releases/v1.0.0:ro
```

### 4. Deploy

```bash
# Build and start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Monitor startup
docker compose logs -f

# Verify health
curl http://localhost/readyz   # should return {"status":"ready"}
curl http://localhost/livez    # should return {"status":"alive"}
```

### 5. SSL/TLS (Recommended)

```bash
# Option A: Let's Encrypt with certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d astrosage.ai -d www.astrosage.ai

# Option B: Cloudflare Origin Certificate (free)
# 1. Generate in Cloudflare SSL/TLS > Origin Server
# 2. Save to ./nginx/certs/ (origin.pem, private_key.pem)
# 3. Mount in docker-compose.prod.yml
```

### 6. Verify Deployment

```bash
# Check all services are healthy
docker compose ps

# Test API
curl https://astrosage.ai/api/v1/health

# Test frontend
curl -I https://astrosage.ai/

# Test search
curl -X POST https://astrosage.ai/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Who is Vishnu?","top_k":3}'
```

## Architecture

```
Client → Nginx (:80/:443)
            ├── /readyz, /livez  → FastAPI (health probes, no rate limit)
            ├── /api/*           → FastAPI (:8000, rate limited)
            ├── /api/v1/chat/completions → SSE streaming (no buffering)
            ├── /_next/static/*  → Next.js static (immutable cache, 1 year)
            ├── /docs, /redoc    → FastAPI docs
            └── /*               → Next.js SSR (:3000)
```

## Services

| Service  | Port      | Purpose                              |
|----------|-----------|--------------------------------------|
| nginx    | 80, 443   | Reverse proxy, SSL, static cache     |
| api      | 8000      | FastAPI knowledge server             |
| frontend | 3000      | Next.js SSR frontend                 |
| redis    | 6379      | Caching, rate limiting, sessions     |
| postgres | 5432      | User data, conversations             |

## Health Checks

| Endpoint   | Purpose      | Expected Response                     |
|------------|-------------|---------------------------------------|
| `/readyz`  | Readiness    | `{"status":"ready"}` or 503          |
| `/livez`   | Liveness     | `{"status":"alive"}`                  |
| `/api/v1/health` | Full health | Component status with version info    |

## Monitoring

### Logs
All services output structured JSON logs to stdout.

```bash
docker compose logs -f api      # API logs
docker compose logs -f nginx    # Access logs
```

### Metrics
Prometheus metrics are available at `/api/v1/metrics` (requires `prometheus-fastapi-instrumentator`).

### Request Tracing
Every request receives an `X-Request-ID` header for tracing. Audit middleware logs every request with latency, method, path, and status code.

## Scaling

### Vertical (single server)
- Increase API workers: set `WORKERS=8` in `.env`
- Increase Nginx worker connections: edit `nginx/nginx.conf`

### Horizontal (multi-server)
- Add a load balancer in front of Nginx
- Use managed Redis and PostgreSQL
- Set up read replicas for PostgreSQL

## Backup

### Database
```bash
# PostgreSQL
docker exec astrosage-postgres pg_dump -U astrosage astrosage > backup_$(date +%Y%m%d).sql

# SQLite (development only)
cp data/astrosage.db backups/astrosage_$(date +%Y%m%d).db
```

### Knowledge Base
The knowledge base is git-versioned (frozen v1.0.0). No separate backup needed.

### Restore
```bash
# PostgreSQL
cat backup_20260720.sql | docker exec -i astrosage-postgres psql -U astrosage astrosage

# SQLite
cp backups/astrosage_20260720.db data/astrosage.db
```

## Recovery

### Container Crash
```yaml
# Docker Compose automatically restarts crashed containers
# (restart: unless-stopped is set on all services)
```

### Full System Recovery
```bash
# 1. Restore database from backup
# 2. Redeploy
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
# 3. Verify
curl http://localhost/readyz
```

### Knowledge Base Corruption
The knowledge base is immutable (frozen release v1.0.0). To recover:
1. Pull the latest repository version
2. Rebuild the Docker image
3. Redeploy

## Troubleshooting

**API won't start:**
```bash
docker compose logs api
# Check for missing knowledge base files or invalid configuration
```

**Frontend shows blank page:**
```bash
docker compose logs frontend
# Check NEXT_PUBLIC_API_URL matches the API server address
```

**Nginx 502 errors:**
```bash
docker compose ps
# Verify api and frontend services are healthy
docker compose logs nginx
```

**Slow search responses:**
- Verify the knowledge base is loaded (check `/readyz`)
- The BM25 index takes 2-3 seconds to load on first request

## Production Checklist

- [ ] Domain purchased and DNS configured
- [ ] SSL certificate installed
- [ ] SECRET_KEY generated (not the default)
- [ ] PostgreSQL password changed
- [ ] CORS origins restricted to actual domain
- [ ] Debug mode disabled (APP_ENVIRONMENT=production)
- [ ] Log level set to WARNING or INFO
- [ ] Backup schedule configured
- [ ] Monitoring set up (optional but recommended)
- [ ] Rate limits adjusted for expected traffic
