# LearnLocal Deployment Guide - Kamatera Cloud

## Overview
This guide will help you deploy LearnLocal on Kamatera cloud infrastructure with optimal configuration for AI workloads and Ollama LLM support.

## Prerequisites
- Kamatera account (sign up at kamatera.com)
- SSH key pair for server access
- Domain name (optional but recommended)

## Step 1: Kamatera Account Setup

### 1.1 Create Kamatera Account
1. Go to [kamatera.com](https://kamatera.com)
2. Sign up for a new account
3. Verify your email and complete account setup
4. Add payment method (credit card or PayPal)

### 1.2 Initial Account Configuration
1. **Login to Console**: https://console.kamatera.com
2. **Set up billing alerts** to monitor usage
3. **Configure SSH keys** in Account Settings → SSH Keys

## Step 2: Server Specifications for LearnLocal

### Recommended Configuration
For optimal performance with Ollama and large language models:

**Minimum Configuration:**
- **CPU**: 4 vCPUs (Intel/AMD)
- **RAM**: 16 GB 
- **Storage**: 100 GB SSD
- **OS**: Ubuntu 24.04 LTS
- **Location**: Choose closest to your users

**Recommended Configuration:**
- **CPU**: 8 vCPUs (Intel/AMD) 
- **RAM**: 32 GB
- **Storage**: 200 GB SSD
- **OS**: Ubuntu 24.04 LTS
- **GPU**: Optional (if available) for faster inference

**Production Configuration:**
- **CPU**: 16 vCPUs
- **RAM**: 64 GB
- **Storage**: 500 GB SSD
- **Load Balancer**: Yes
- **Backup**: Daily automated backups

## Step 3: Create Kamatera Server

### 3.1 Server Creation
1. **Login** to Kamatera Console
2. **Navigate** to "Cloud Servers" → "Create Server"
3. **Configure Server**:
   ```
   Server Name: learnlocal-production
   Location: [Choose your preferred datacenter]
   Image: Ubuntu Server 24.04 LTS x64
   CPU: 8 Type A (or higher)
   RAM: 32768 MB
   SSD: 200 GB
   Network: 1000 Mbps
   ```
4. **SSH Key**: Select your uploaded SSH key
5. **Firewall**: Create custom rules (see below)
6. **Click "Create Server"**

### 3.2 Firewall Configuration
Create the following firewall rules:

```
Inbound Rules:
- SSH (22) - Your IP only
- HTTP (80) - Anywhere
- HTTPS (443) - Anywhere
- Custom (8000) - Anywhere (for API)
- Custom (11434) - Localhost only (for Ollama)

Outbound Rules:
- All traffic - Anywhere (for package downloads)
```

## Step 4: Server Initial Setup

### 4.1 Connect to Server
```bash
# Replace with your server IP
ssh root@YOUR_SERVER_IP
```

### 4.2 Initial System Setup
```bash
# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git vim htop unzip software-properties-common

# Create non-root user
useradd -m -s /bin/bash learnlocal
usermod -aG sudo learnlocal
mkdir -p /home/learnlocal/.ssh
cp /root/.ssh/authorized_keys /home/learnlocal/.ssh/
chown -R learnlocal:learnlocal /home/learnlocal/.ssh
chmod 700 /home/learnlocal/.ssh
chmod 600 /home/learnlocal/.ssh/authorized_keys

# Switch to new user
su - learnlocal
```

## Step 5: Install Dependencies

### 5.1 Install Python 3.11+
```bash
# Python 3.12 comes pre-installed on Ubuntu 24.04
sudo apt update

# Install Python development tools and venv
sudo apt install -y python3-venv python3-dev python3-pip

# Verify Python version (should be 3.12+)
python3 --version
```

### 5.2 Install Node.js (for npm if needed)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 5.3 Install Docker (Optional for containerized deployment)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker learnlocal
```

## Step 6: Install Ollama

### 6.1 Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify installation
ollama --version
```

### 6.2 Configure Ollama
```bash
# Create ollama service override
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Configure Ollama to bind to all interfaces
sudo tee /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
EOF

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Download both models for dynamic switching
ollama pull llama3:8b
ollama pull gpt-oss:20b
```

## Step 7: Deploy LearnLocal Application

### 7.1 Clone Repository
```bash
# Clone your repository
cd /home/learnlocal
git clone https://github.com/Animesh-Uttekar/learnerexpert.git learnlocal
cd learnlocal
```

### 7.2 Set up Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 7.3 Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Production Environment Configuration (.env):**
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Ollama Configuration
OFFLINE_LLM_ENABLED=true
OFFLINE_LLM_PROVIDER=ollama
OFFLINE_LLM_MODEL=gpt-oss:20b
OLLAMA_MODELS="llama3:8b,gpt-oss:20b"
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (Optional fallback)
OPENAI_API_KEY=your-openai-key-if-needed

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/learnlocal.db

# TTS Configuration
TTS_ENABLED=true
TTS_DEFAULT_ENGINE=pyttsx3

# Security
FRONTEND_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

## Step 8: Configure System Services

### 8.1 Create Systemd Service
```bash
sudo tee /etc/systemd/system/learnlocal.service << EOF
[Unit]
Description=LearnLocal AI Education Platform
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=exec
User=learnlocal
WorkingDirectory=/home/learnlocal/learnlocal
Environment="PATH=/home/learnlocal/learnlocal/venv/bin"
ExecStart=/home/learnlocal/learnlocal/venv/bin/python main.py
Restart=always
RestartSec=10

# Logging
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=learnlocal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable learnlocal
sudo systemctl start learnlocal

# Check status
sudo systemctl status learnlocal
```

## Step 9: Configure Nginx Reverse Proxy

### 9.1 Install Nginx
```bash
sudo apt install -y nginx
```

### 9.2 Configure Nginx
```bash
sudo tee /etc/nginx/sites-available/learnlocal << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host \$host;
    }

    # Root
    location / {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/learnlocal /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Step 10: SSL Certificate with Let's Encrypt

### 10.1 Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 10.2 Obtain SSL Certificate
```bash
# Replace with your domain
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Step 11: Monitoring and Logging

### 11.1 Install Monitoring Tools
```bash
# Install htop, iotop for system monitoring
sudo apt install -y htop iotop nethogs

# Install log rotation
sudo apt install -y logrotate
```

### 11.2 Configure Log Rotation
```bash
sudo tee /etc/logrotate.d/learnlocal << EOF
/home/learnlocal/learnlocal/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 learnlocal learnlocal
    postrotate
        systemctl reload learnlocal
    endscript
}
EOF
```

## Step 12: Backup Strategy

### 12.1 Automated Backup Script
```bash
sudo tee /home/learnlocal/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/learnlocal/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

# Backup database
cp /home/learnlocal/learnlocal/data/learnlocal.db \$BACKUP_DIR/learnlocal_\$DATE.db

# Backup configuration
tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz /home/learnlocal/learnlocal/.env /home/learnlocal/learnlocal/data/

# Keep only last 30 days of backups
find \$BACKUP_DIR -name "*.db" -mtime +30 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x /home/learnlocal/backup.sh

# Add to crontab
echo "0 2 * * * /home/learnlocal/backup.sh >> /var/log/backup.log 2>&1" | crontab -
```

## Step 13: Testing Deployment

### 13.1 Test Services
```bash
# Check all services
sudo systemctl status ollama
sudo systemctl status learnlocal
sudo systemctl status nginx

# Test API endpoints
curl http://localhost:8000/api/health
curl http://your-domain.com/api/health

# Test HTTPS
curl https://your-domain.com/api/health
```

### 13.2 Performance Testing
```bash
# Monitor system resources
htop

# Check Ollama model
ollama list

# Test API response time
curl -w "%{time_total}s\n" -s -o /dev/null http://localhost:8000/api/health
```

## Step 14: Security Hardening

### 14.1 Firewall Configuration
```bash
# Install UFW
sudo apt install -y ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 14.2 SSH Hardening
```bash
sudo tee -a /etc/ssh/sshd_config << EOF
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

sudo systemctl restart sshd
```

## Step 15: Scaling and Optimization

### 15.1 Performance Tuning
```bash
# Increase file limits
sudo tee -a /etc/security/limits.conf << EOF
learnlocal soft nofile 65536
learnlocal hard nofile 65536
learnlocal soft nproc 32768
learnlocal hard nproc 32768
EOF

# System optimization
sudo tee -a /etc/sysctl.conf << EOF
vm.swappiness=10
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 65536 134217728
net.ipv4.tcp_wmem=4096 65536 134217728
EOF

sudo sysctl -p
```

## Maintenance Commands

### Daily Operations
```bash
# Check system status
sudo systemctl status learnlocal ollama nginx

# Check logs
sudo journalctl -u learnlocal -f
sudo journalctl -u ollama -f
sudo tail -f /var/log/nginx/access.log

# Update application
cd /home/learnlocal/learnlocal
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart learnlocal

# Monitor resources
htop
df -h
free -h
```

### Troubleshooting
```bash
# If service fails to start
sudo systemctl restart ollama
sudo systemctl restart learnlocal
sudo systemctl restart nginx

# Check port usage
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :11434

# Check model status
ollama list
ollama ps
```

## Cost Optimization

### Monthly Estimate (Kamatera)
- **8 vCPU, 32GB RAM, 200GB SSD**: ~$150-200/month
- **Load Balancer**: ~$15/month
- **Backup Storage**: ~$10/month
- **Bandwidth**: Variable based on usage

### Cost Savings Tips
1. Use reserved instances for predictable workloads
2. Implement auto-scaling during off-peak hours
3. Regular cleanup of logs and temporary files
4. Monitor and optimize resource usage

## Support and Documentation

- **Kamatera Support**: support@kamatera.com
- **Documentation**: https://www.kamatera.com/support/
- **Server Management**: https://console.kamatera.com
- **LearnLocal Issues**: https://github.com/Animesh-Uttekar/learnlocal/issues

Your LearnLocal application is now successfully deployed on Kamatera with production-grade configuration!