# Stubble2Power — Production Operations & Deployment Runbook

**Document ID:** S2P-DOC-DEP-RUN-2026-V1  
**Classification:** Site Reliability & DevOps Operations  
**Platform Version:** v2.5.0  

---

## 1. Pre-Deployment Verification Checklist

Before initiating production deployment, ensure the following prerequisites are met:
- [ ] Docker Engine 24.0+ and Docker Compose v2.20+ installed.
- [ ] Host kernel supports cgroups v2 for container resource limits.
- [ ] Production domain DNS records configured (`s2p.yourdomain.com`).
- [ ] Valid SSL/TLS certificate acquired (Let's Encrypt / Certbot).
- [ ] NASA FIRMS MAP Key acquired and validated.
- [ ] Strong production secrets generated:
  ```bash
  # Generate cryptographically secure JWT Secret (64 hex characters)
  openssl rand -hex 32

  # Generate secure PostgreSQL password
  openssl rand -base64 24
  ```

---

## 2. Environment Configuration

Create `/etc/stubble2power/.env.production` (permissions `chmod 600`):

```bash
# Application Environment Mode
APP_ENV=production
LOG_LEVEL=INFO

# PostgreSQL Configuration
POSTGRES_DB=stubble2power_prod
POSTGRES_USER=s2p_admin
POSTGRES_PASSWORD=YOUR_HIGH_ENTROPY_POSTGRES_PASSWORD_HERE

# Production Database Connection String
DATABASE_URL=postgresql+psycopg2://s2p_admin:YOUR_HIGH_ENTROPY_POSTGRES_PASSWORD_HERE@db:5432/stubble2power_prod

# Enterprise Authentication & Security (Must be >= 32 chars, unique)
JWT_SECRET_KEY=YOUR_CRYPTOGRAPHICALLY_SECURE_JWT_SECRET_KEY_HERE
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_BCRYPT_ROUNDS=12
PBKDF2_ROUNDS=100000

# External Satellite Intelligence
NASA_FIRMS_MAP_KEY=YOUR_OFFICIAL_NASA_FIRMS_MAP_KEY_HERE

# Production Seeding Safeguard (Defaults to false)
ALLOW_PRODUCTION_SEED=false
```

---

## 3. Step-by-Step Production Deployment

### Step 3.1: Build and Validate Images
```bash
# Pull latest code
git checkout main && git pull origin main

# Build hardened production images
docker compose -f docker-compose.prod.yml --env-file /etc/stubble2power/.env.production build --no-cache
```

### Step 3.2: Initialize and Migrate Database
```bash
# Start PostGIS database container
docker compose -f docker-compose.prod.yml --env-file /etc/stubble2power/.env.production up -d db

# Wait for database healthcheck
until docker exec stubble2power-prod-db pg_isready -U s2p_admin -d stubble2power_prod; do
  echo "Waiting for database to become ready..."
  sleep 2
done

# Run database migrations (or initial schema build)
docker compose -f docker-compose.prod.yml --env-file /etc/stubble2power/.env.production run --rm backend python -c "
from backend.models.entities import Base
from backend.core.database.engine import engine
Base.metadata.create_all(bind=engine)
print('Database schema synchronized.')
"
```

### Step 3.3: Launch Complete Application Stack
```bash
docker compose -f docker-compose.prod.yml --env-file /etc/stubble2power/.env.production up -d
```

### Step 3.4: Verify Container Health
```bash
docker compose -f docker-compose.prod.yml ps
```
Expected output:
```
NAME                           COMMAND                  SERVICE    STATUS
stubble2power-prod-backend     "uvicorn backend.mai…"   backend    running (healthy)
stubble2power-prod-db          "docker-entrypoint.s…"   db         running (healthy)
stubble2power-prod-frontend    "streamlit run app.p…"   frontend   running (healthy)
```

---

## 4. Reverse Proxy & TLS Configuration (Nginx)

Place this configuration in `/etc/nginx/sites-available/stubble2power.conf`:

```nginx
upstream s2p_frontend {
    server 127.0.0.1:8501;
}

upstream s2p_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name s2p.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name s2p.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/s2p.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/s2p.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; connect-src 'self' wss: https:;" always;

    # Backend API Routing
    location /api/ {
        proxy_pass http://s2p_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Documentation
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://s2p_backend;
        proxy_set_header Host $host;
    }

    # Streamlit Frontend with WebSocket Support
    location / {
        proxy_pass http://s2p_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

## 5. Automated Backup Schedule & Maintenance

Configure a daily automated backup cron job at 02:00 UTC under root:

```bash
# Add to /etc/cron.d/s2p_backup
0 2 * * * root cd /opt/stubble2power && /opt/stubble2power/venv/bin/python scripts/backup_db.py --backup-dir /var/backups/stubble2power --retention-days 30 >> /var/log/s2p_backup.log 2>&1
```

---

## 6. Disaster Recovery & Restoration Protocol

In the event of database corruption, accidental loss, or hardware failure:

### Step 6.1: Identify the Latest Validated Backup
```bash
ls -lt /var/backups/stubble2power/s2p_backup_*
```

### Step 6.2: Execute Decryption, Checksum Validation, and Restoration
```bash
# Ensure BACKUP_ENCRYPTION_KEY is set in environment or supplied via --key
export BACKUP_ENCRYPTION_KEY="your-secret-base64-fernet-key"

# Perform dry-run cryptographic integrity verification first
python scripts/restore_db.py /var/backups/stubble2power/s2p_backup_postgresql_20261114_020000.enc --dry-run

# Execute full restore with mandatory --confirm-destructive and comprehensive post-restore validation
python scripts/restore_db.py /var/backups/stubble2power/s2p_backup_postgresql_20261114_020000.enc --confirm-destructive --target-db-url "$DATABASE_URL"
```

---

## 7. Zero-Downtime Rolling Upgrade & Emergency Rollback

### Rolling Upgrade:
```bash
# 1. Pull new code & build new container image
docker compose -f docker-compose.prod.yml build backend frontend

# 2. Re-create containers with zero downtime
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

### Emergency Rollback:
```bash
# 1. Checkout previous stable release tag
git checkout v2.4.0

# 2. Rebuild and restart stack
docker compose -f docker-compose.prod.yml up -d --build
```
