# AstroSage AI — Deployment Guide

## Quick Start (Development)

```bash
# Clone and start everything
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-
docker compose up --build

# Or run without Docker
make dev
```

## Production Deployment

### 1. Server Setup

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Clone the repository
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-
```

### 2. Configure Environment

```bash
# Copy the production template
cp .env.production .env

# Generate a secure secret key
openssl rand -hex 32

# Edit .env with your values
nano .env
```

### 3. Deploy

```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify health
curl http://localhost/api/v1/health

# View logs
docker compose logs -f
```

### 4. SSL/TLS (Recommended)

For production with a domain:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d astrosage.ai -d www.astrosage.ai
```

Or use Cloudflare/DigitalOcean load balancer for SSL termination.

## Architecture

```
Client → Nginx (:80/:443)
            ├── /api/*    → FastAPI (:8000)
            ├── /docs/*   → FastAPI docs
            ├── /mcp/*    → SSE endpoint
            └── /*        → Next.js (:3000)
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80, 443 | Reverse proxy, static assets, SSL |
| api | 8000 | FastAPI knowledge server |
| frontend | 3000 | Next.js SSR frontend |
| redis | 6379 | Caching, rate limiting, sessions |
| postgres | 5432 | User data, conversations |

## Health Checks

- API: `GET /api/v1/health`
- Frontend: `GET /` (returns HTML)
- Redis: `redis-cli ping`
- PostgreSQL: `pg_isready -U astrosage`

## Monitoring

The API exposes:
- Structured JSON logs (stdout)
- Prometheus metrics at `/api/v1/metrics`
- Request IDs for tracing (`X-Request-ID` header)
- Audit logs with latency and user tracking

## Backup

```bash
# Database backup
docker exec astrosage-postgres pg_dump -U astrosage astrosage > backup.sql

# Knowledge base (read-only in production)
# No backup needed — frozen v1.0.0 is in the Git repository
```

## Scaling

For higher traffic:
1. Add more API workers: `WORKERS=8`
2. Scale horizontally with a load balancer
3. Move Redis to a managed service
4. Consider Kubernetes for 100+ concurrent users
