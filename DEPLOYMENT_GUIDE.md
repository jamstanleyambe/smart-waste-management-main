# 🚀 Smart Waste Management System - Deployment Guide

## 📋 Table of Contents
1. [Development Deployment](#development-deployment)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Security Considerations](#security-considerations)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## 🛠️ Development Deployment

### Quick Start
```bash
# Clone repository
git clone https://github.com/jamstanleyambe/smart-waste-management-main.git
cd smart-waste-management-main

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_camera.txt

# Setup database
python manage.py migrate
python manage.py createsuperuser

# Start servers
python manage.py runserver 0.0.0.0:8000 &
streamlit run route_dashboard.py --server.port 8502 --server.address 0.0.0.0 &
```

### Development URLs
- **Django Admin**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/
- **Dashboard**: http://localhost:8502/

---

## 🏭 Production Deployment

### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.12+
- PostgreSQL 13+
- Nginx
- SSL certificate (Let's Encrypt recommended)

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.12 python3.12-venv python3.12-dev postgresql postgresql-contrib nginx git -y

# Install system dependencies for image processing
sudo apt install libjpeg-dev zlib1g-dev libpng-dev -y
```

### 2. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE smart_waste_db;
CREATE USER waste_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE smart_waste_db TO waste_user;
\q
```

### 3. Application Deployment
```bash
# Create application directory
sudo mkdir -p /opt/smart-waste-management
sudo chown $USER:$USER /opt/smart-waste-management
cd /opt/smart-waste-management

# Clone repository
git clone https://github.com/jamstanleyambe/smart-waste-management-main.git .

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_camera.txt
pip install gunicorn psycopg2-binary

# Configure environment
cp .env.example .env
nano .env
```

### 4. Environment Configuration
```bash
# .env file
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://waste_user:secure_password@localhost/smart_waste_db
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
STATIC_ROOT=/opt/smart-waste-management/staticfiles
MEDIA_ROOT=/opt/smart-waste-management/media
```

### 5. Django Configuration
```bash
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Test configuration
python manage.py check --deploy
```

### 6. Gunicorn Configuration
```bash
# Create Gunicorn configuration
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
user = "www-data"
group = "www-data"
tmp_upload_dir = None
EOF
```

### 7. Systemd Services
```bash
# Django service
sudo tee /etc/systemd/system/smart-waste-django.service > /dev/null << EOF
[Unit]
Description=Smart Waste Management Django App
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/smart-waste-management
Environment=PATH=/opt/smart-waste-management/venv/bin
ExecStart=/opt/smart-waste-management/venv/bin/gunicorn --config gunicorn.conf.py waste_management.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Streamlit service
sudo tee /etc/systemd/system/smart-waste-streamlit.service > /dev/null << EOF
[Unit]
Description=Smart Waste Management Streamlit Dashboard
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/smart-waste-management
Environment=PATH=/opt/smart-waste-management/venv/bin
ExecStart=/opt/smart-waste-management/venv/bin/streamlit run route_dashboard.py --server.port 8502 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable smart-waste-django
sudo systemctl enable smart-waste-streamlit
sudo systemctl start smart-waste-django
sudo systemctl start smart-waste-streamlit
```

### 8. Nginx Configuration
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/smart-waste-management > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 10M;

    # Django API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Streamlit Dashboard
    location / {
        proxy_pass http://127.0.0.1:8502;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static/ {
        alias /opt/smart-waste-management/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/smart-waste-management/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/smart-waste-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. SSL Certificate
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 🐳 Docker Deployment

### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: smart_waste_db
      POSTGRES_USER: waste_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  django:
    build: .
    command: gunicorn waste_management.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://waste_user:secure_password@db:5432/smart_waste_db
      - REDIS_URL=redis://redis:6379/0

  streamlit:
    build: .
    command: streamlit run route_dashboard.py --server.port 8502 --server.address 0.0.0.0 --server.headless true
    volumes:
      - .:/app
    ports:
      - "8502:8502"
    depends_on:
      - django

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - django
      - streamlit

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements_camera.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements_camera.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p staticfiles media

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000 8502

CMD ["gunicorn", "waste_management.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser

# View logs
docker-compose logs -f
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance Setup
```bash
# Launch Ubuntu 20.04 LTS instance
# Security groups: HTTP (80), HTTPS (443), SSH (22)

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Follow production deployment steps above
```

#### 2. RDS Database Setup
```bash
# Create RDS PostgreSQL instance
# Update DATABASE_URL in .env file
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/smart_waste_db
```

#### 3. S3 for Media Files
```python
# settings_production.py
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'us-east-1'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Google Cloud Platform

#### 1. App Engine Deployment
```yaml
# app.yaml
runtime: python312
env: standard

handlers:
- url: /static
  static_dir: staticfiles
- url: /media
  static_dir: media
- url: /.*
  script: auto

env_variables:
  DEBUG: "False"
  DATABASE_URL: "postgresql://user:pass@/db?host=/cloudsql/project:region:instance"
```

#### 2. Cloud SQL Setup
```bash
# Create Cloud SQL instance
gcloud sql instances create smart-waste-db --database-version=POSTGRES_13 --tier=db-f1-micro

# Create database
gcloud sql databases create smart_waste_db --instance=smart-waste-db
```

### Azure Deployment

#### 1. App Service Setup
```bash
# Create App Service
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name myAppName --runtime "PYTHON|3.12"

# Configure environment variables
az webapp config appsettings set --resource-group myResourceGroup --name myAppName --settings DEBUG=False DATABASE_URL="your-connection-string"
```

---

## ⚙️ Environment Configuration

### Development Environment
```bash
# .env.development
DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Staging Environment
```bash
# .env.staging
DEBUG=False
SECRET_KEY=staging-secret-key
DATABASE_URL=postgresql://user:pass@staging-db:5432/smart_waste_db
ALLOWED_HOSTS=staging.your-domain.com
```

### Production Environment
```bash
# .env.production
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:pass@prod-db:5432/smart_waste_db
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

---

## 🔒 Security Considerations

### 1. Django Security
```python
# settings_production.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
```

### 2. Database Security
```bash
# PostgreSQL security
sudo -u postgres psql
ALTER USER waste_user PASSWORD 'very-secure-password';
REVOKE ALL ON DATABASE smart_waste_db FROM PUBLIC;
GRANT CONNECT ON DATABASE smart_waste_db TO waste_user;
\q
```

### 3. Firewall Configuration
```bash
# UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw deny 8000  # Block direct access to Django
sudo ufw deny 8502  # Block direct access to Streamlit
```

### 4. SSL/TLS Configuration
```bash
# Strong SSL configuration in Nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

---

## 📊 Monitoring & Logging

### 1. Application Logging
```python
# settings_production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/smart-waste/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### 2. System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Create log rotation
sudo tee /etc/logrotate.d/smart-waste > /dev/null << EOF
/var/log/smart-waste/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload smart-waste-django
    endscript
}
EOF
```

### 3. Health Checks
```python
# health_check.py
import requests
import sys

def check_django():
    try:
        response = requests.get('http://localhost:8000/api/bin-data/', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_streamlit():
    try:
        response = requests.get('http://localhost:8502/', timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    django_ok = check_django()
    streamlit_ok = check_streamlit()
    
    if not django_ok or not streamlit_ok:
        sys.exit(1)
    else:
        sys.exit(0)
```

---

## 💾 Backup & Recovery

### 1. Database Backup
```bash
# Create backup script
cat > backup_db.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/smart-waste"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

# Database backup
pg_dump -h localhost -U waste_user smart_waste_db > \$BACKUP_DIR/db_backup_\$DATE.sql

# Media files backup
tar -czf \$BACKUP_DIR/media_backup_\$DATE.tar.gz /opt/smart-waste-management/media/

# Keep only last 30 days
find \$BACKUP_DIR -name "*.sql" -mtime +30 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x backup_db.sh

# Schedule daily backups
echo "0 2 * * * /opt/backups/smart-waste/backup_db.sh" | crontab -
```

### 2. Recovery Process
```bash
# Restore database
psql -h localhost -U waste_user smart_waste_db < backup_file.sql

# Restore media files
tar -xzf media_backup.tar.gz -C /

# Restart services
sudo systemctl restart smart-waste-django
sudo systemctl restart smart-waste-streamlit
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Django Service Won't Start
```bash
# Check service status
sudo systemctl status smart-waste-django

# Check logs
sudo journalctl -u smart-waste-django -f

# Check configuration
python manage.py check --deploy
```

#### 2. Database Connection Issues
```bash
# Test database connection
python manage.py dbshell

# Check PostgreSQL status
sudo systemctl status postgresql

# Check database permissions
sudo -u postgres psql -c "\du"
```

#### 3. Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Check file permissions
sudo chown -R www-data:www-data /opt/smart-waste-management/staticfiles
```

#### 4. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect your-domain.com:443
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_bin_fill_level ON core_bin(fill_level);
CREATE INDEX idx_bin_location ON core_bin(latitude, longitude);
CREATE INDEX idx_camera_image_created ON core_cameraimage(created_at);
```

#### 2. Caching Configuration
```python
# settings_production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

#### 3. Gunicorn Optimization
```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = (2 * multiprocessing.cpu_count()) + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

---

## 📚 Additional Resources

- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Gunicorn Configuration**: https://docs.gunicorn.org/en/stable/configure.html
- **Nginx Configuration**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Docker Documentation**: https://docs.docker.com/

---

**🚀 Your Smart Waste Management System is now production-ready!**
