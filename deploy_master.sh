#!/bin/bash

# 🚀 Smart Waste Management System - Master Branch Deployment Script
# This script deploys the production-ready version to your server

set -e  # Exit on any error

echo "🚀 Starting deployment of Smart Waste Management System (Master Branch)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smart-waste-management"
PROJECT_DIR="/opt/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_DIR="$PROJECT_DIR/logs"

# Create necessary directories
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
sudo mkdir -p $PROJECT_DIR $BACKUP_DIR $LOG_DIR

# Backup existing installation if it exists
if [ -d "$PROJECT_DIR/app" ]; then
    echo -e "${YELLOW}💾 Creating backup of existing installation...${NC}"
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    sudo cp -r $PROJECT_DIR/app $BACKUP_DIR/$BACKUP_NAME
    echo -e "${GREEN}✅ Backup created: $BACKUP_DIR/$BACKUP_NAME${NC}"
fi

# Clone or update repository
if [ ! -d "$PROJECT_DIR/repo" ]; then
    echo -e "${BLUE}📥 Cloning repository...${NC}"
    sudo git clone https://github.com/jamstanleyambe/smart-waste-management-main.git $PROJECT_DIR/repo
else
    echo -e "${BLUE}📥 Updating repository...${NC}"
    cd $PROJECT_DIR/repo
    sudo git fetch origin
    sudo git checkout master
    sudo git pull origin master
fi

# Switch to master branch
cd $PROJECT_DIR/repo
sudo git checkout master

# Create virtual environment
echo -e "${BLUE}🐍 Setting up Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    sudo python3 -m venv $VENV_DIR
fi

# Activate virtual environment and install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
source $VENV_DIR/bin/activate
sudo $VENV_DIR/bin/pip install --upgrade pip
sudo $VENV_DIR/bin/pip install -r requirements_production.txt

# Set environment variables
echo -e "${BLUE}🔧 Setting environment variables...${NC}"
export DJANGO_SETTINGS_MODULE=waste_management.settings_production
export SECRET_KEY="$(openssl rand -hex 50)"
export DEBUG=False
export DATABASE_URL="postgresql://user:password@localhost/smart_waste_db"

# Create .env file
sudo tee $PROJECT_DIR/.env > /dev/null << EOF
DJANGO_SETTINGS_MODULE=waste_management.settings_production
SECRET_KEY=$SECRET_KEY
DEBUG=False
DATABASE_URL=$DATABASE_URL
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
EOF

# Run Django migrations
echo -e "${BLUE}🗄️ Running database migrations...${NC}"
cd $PROJECT_DIR/repo
sudo $VENV_DIR/bin/python manage.py migrate --settings=waste_management.settings_production

# Collect static files
echo -e "${BLUE}📁 Collecting static files...${NC}"
sudo $VENV_DIR/bin/python manage.py collectstatic --noinput --settings=waste_management.settings_production

# Create superuser if it doesn't exist
echo -e "${BLUE}👤 Setting up admin user...${NC}"
sudo $VENV_DIR/bin/python manage.py shell --settings=waste_management.settings_production << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Admin user created successfully')
else:
    print('Admin user already exists')
EOF

# Seed sample data
echo -e "${BLUE}🌱 Seeding sample data...${NC}"
sudo $VENV_DIR/bin/python manage.py seed_bins --settings=waste_management.settings_production
sudo $VENV_DIR/bin/python manage.py seed_trucks --settings=waste_management.settings_production
sudo $VENV_DIR/bin/python manage.py seed_dumpingspots --settings=waste_management.settings_production

# Create systemd service files
echo -e "${BLUE}🔧 Creating systemd services...${NC}"

# Django service
sudo tee /etc/systemd/system/smart-waste-django.service > /dev/null << EOF
[Unit]
Description=Smart Waste Management Django API
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR/repo
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/python manage.py runserver 0.0.0.0:8000 --settings=waste_management.settings_production
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
WorkingDirectory=$PROJECT_DIR/repo
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/streamlit run route_dashboard.py --server.port 8502 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
echo -e "${BLUE}🔄 Enabling systemd services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable smart-waste-django
sudo systemctl enable smart-waste-streamlit

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
sudo systemctl start smart-waste-django
sudo systemctl start smart-waste-streamlit

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${BLUE}📊 Checking service status...${NC}"
sudo systemctl status smart-waste-django --no-pager -l
sudo systemctl status smart-waste-streamlit --no-pager -l

# Test API endpoints
echo -e "${BLUE}🧪 Testing API endpoints...${NC}"
if curl -s http://localhost:8000/api/bin-data/ | grep -q "BIN001"; then
    echo -e "${GREEN}✅ Django API is working correctly${NC}"
else
    echo -e "${RED}❌ Django API test failed${NC}"
fi

if curl -s http://localhost:8502/ | grep -q "Streamlit"; then
    echo -e "${GREEN}✅ Streamlit dashboard is working correctly${NC}"
else
    echo -e "${RED}❌ Streamlit dashboard test failed${NC}"
fi

# Create Nginx configuration
echo -e "${BLUE}🌐 Creating Nginx configuration...${NC}"
sudo tee /etc/nginx/sites-available/smart-waste-management > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

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
}
EOF

# Enable Nginx site
echo -e "${BLUE}🔗 Enabling Nginx site...${NC}"
sudo ln -sf /etc/nginx/sites-available/smart-waste-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Create deployment summary
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo -e "   • Project Directory: $PROJECT_DIR"
echo -e "   • Virtual Environment: $VENV_DIR"
echo -e "   • Django API: http://localhost:8000"
echo -e "   • Streamlit Dashboard: http://localhost:8502"
echo -e "   • Admin Interface: http://localhost:8000/admin/"
echo -e "   • Admin Credentials: admin / admin123"
echo -e "   • Services: smart-waste-django, smart-waste-streamlit"
echo -e "   • Nginx: Configured and enabled"
echo -e ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo -e "   1. Update domain names in Nginx configuration"
echo -e "   2. Obtain SSL certificate with Let's Encrypt"
echo -e "   3. Configure firewall rules"
echo -e "   4. Set up monitoring and logging"
echo -e "   5. Test all endpoints and functionality"
echo -e ""
echo -e "${GREEN}🚀 Your Smart Waste Management System is now deployed and running!${NC}"
