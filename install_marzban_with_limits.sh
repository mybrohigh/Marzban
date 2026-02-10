#!/bin/bash

# Marzban Installation Script with Advanced Limits System
# Enhanced version with limits management and monitoring
# Compatible with Ubuntu/Debian systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="mybrohigh"
REPO_NAME="Marzban"
SCRIPT_NAME="marzban.sh"
INSTALL_DIR="/opt/marzban"
SERVICE_NAME="marzban"
PYTHON_VERSION="3.12"

# Print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print header
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}                         ${GREEN}Marzban with Advanced Limits System${NC}                         ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}                                   ${YELLOW}Enhanced Version${NC}                                   ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}                         ${GREEN}https://github.com/${REPO_OWNER}/${REPO_NAME}${NC}                         ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_color "$RED" "Error: This script must be run as root!"
        echo "Please use: sudo bash $0"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/debian_version ]]; then
        OS="debian"
        PKG_MANAGER="apt"
    elif [[ -f /etc/lsb-release && $(grep -qi "ubuntu" /etc/lsb-release) ]]; then
        OS="ubuntu"
        PKG_MANAGER="apt"
    elif [[ -f /etc/centos-release ]]; then
        OS="centos"
        PKG_MANAGER="yum"
    elif [[ -f /etc/fedora-release ]]; then
        OS="fedora"
        PKG_MANAGER="dnf"
    else
        print_color "$RED" "Error: Unsupported operating system"
        echo "Supported: Ubuntu, Debian, CentOS, Fedora"
        exit 1
    fi
    
    print_color "$GREEN" "Detected OS: $OS"
}

# Install system dependencies
install_dependencies() {
    print_color "$YELLOW" "Installing system dependencies..."
    
    case $PKG_MANAGER in
        apt)
            apt update
            apt install -y \
                curl \
                wget \
                unzip \
                tar \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                sqlite3 \
                nginx \
                supervisor \
                systemd \
                sqlite3
            ;;
        yum)
            yum update -y
            yum install -y \
                curl \
                wget \
                unzip \
                tar \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                sqlite \
                nginx \
                supervisor \
                systemd
            ;;
        dnf)
            dnf update -y
            dnf install -y \
                curl \
                wget \
                unzip \
                tar \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                sqlite \
                nginx \
                supervisor \
                systemd
            ;;
    esac
    
    print_color "$GREEN" "✓ System dependencies installed"
}

# Create installation directory
create_install_dir() {
    print_color "$YELLOW" "Creating installation directory..."
    
    if [[ -d $INSTALL_DIR ]]; then
        print_color "$YELLOW" "Directory $INSTALL_DIR already exists. Backing up..."
        mv $INSTALL_DIR ${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    mkdir -p $INSTALL_DIR
    cd $INSTALL_DIR
    print_color "$GREEN" "✓ Installation directory created: $INSTALL_DIR"
}

# Download Marzban with limits
download_marzban() {
    print_color "$YELLOW" "Downloading Marzban with limits system..."
    
    # Download full repo (includes alembic.ini and migrations)
    curl -L "https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/master.tar.gz" \
        | tar -xz --strip-components=1 -C "$INSTALL_DIR"
    
    chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
    chmod +x "$INSTALL_DIR/install_latest_xray.sh"
    
    print_color "$GREEN" "✓ Marzban with limits downloaded"
}

# Setup Python environment
setup_python_env() {
    print_color "$YELLOW" "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    pip install -r requirements.txt
    
    # Install additional dependencies for limits system
    pip install aiohttp sqlalchemy alembic
    
    print_color "$GREEN" "✓ Python environment setup complete"
}

# Create database
setup_database() {
    print_color "$YELLOW" "Setting up database..."
    
    # Ensure setuptools (pkg_resources) is available
    python - <<'PY'
try:
    import pkg_resources  # noqa: F401
except Exception:
    raise SystemExit(1)
PY
    if [[ $? -ne 0 ]]; then
        pip install --upgrade setuptools
    fi
    
    # Create database directory
    mkdir -p /var/lib/marzban
    
    # Run database migrations
    alembic -c "$INSTALL_DIR/alembic.ini" upgrade head
    
    print_color "$GREEN" "✓ Database setup complete"
}

# Create systemd service
create_service() {
    print_color "$YELLOW" "Creating systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Marzban with Limits
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${INSTALL_DIR}/venv/bin
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    
    print_color "$GREEN" "✓ Systemd service created"
}

# Setup configuration
setup_config() {
    print_color "$YELLOW" "Setting up configuration..."
    
    # Create .env file if not exists
    if [[ ! -f $INSTALL_DIR/.env ]]; then
        cat > $INSTALL_DIR/.env << EOF
# Marzban Configuration with Limits
# Generated by install script on $(date)

# Database Configuration
SQLALCHEMY_DATABASE_URL=sqlite:///var/lib/marzban/app.db

# Application Configuration
DEBUG=false
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# XRay Configuration
XRAY_JSON_PATH=/var/lib/marzban/xray_config.json

# Limits System Configuration
LIMITS_MONITOR_ENABLED=true
LIMITS_CHECK_INTERVAL=300
LIMITS_NOTIFICATION_THRESHOLD=0.8

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)

# Subscription Configuration
XRAY_SUBSCRIPTION_PATH=sub
XRAY_SUBSCRIPTION_URL_PREFIX=https://your-domain.com

# Telegram Bot (Optional)
# TELEGRAM_BOT_TOKEN=your_bot_token
# TELEGRAM_ADMIN_CHAT_ID=your_chat_id

# Discord Webhook (Optional)
# DISCORD_WEBHOOK_URL=your_webhook_url

# Email Notifications (Optional)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_app_password
# SMTP_FROM_EMAIL=your_email@gmail.com
EOF
        
        print_color "$GREEN" "✓ Configuration file created"
        print_color "$YELLOW" "⚠ Please edit $INSTALL_DIR/.env with your settings"
    else
        print_color "$BLUE" "✓ Configuration file already exists"
    fi
}

# Setup log rotation
setup_logrotate() {
    print_color "$YELLOW" "Setting up log rotation..."
    
    cat > /etc/logrotate.d/marzban << EOF
/var/log/marzban/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload marzban
}
EOF
    
    print_color "$GREEN" "✓ Log rotation configured"
}

# Create admin user
create_admin() {
    print_color "$YELLOW" "Creating admin user..."
    
    # Check if admin already exists
    if [[ -f /var/lib/marzban/app.db ]]; then
        cd $INSTALL_DIR
        source venv/bin/activate
        
        # Create default admin if not exists
        python -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('/var/lib/marzban/app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM admins WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        import secrets
        password = secrets.token_urlsafe(12)
        cursor.execute('INSERT INTO admins (username, password, is_sudo) VALUES (?, ?, ?)', 
                   ('admin', password, True))
        conn.commit()
        print(f'✓ Admin user created: admin / {password}')
    else:
        print('✓ Admin user already exists')
    conn.close()
except Exception as e:
    print(f'Error creating admin: {e}')
    sys.exit(1)
"
    fi
    
    print_color "$GREEN" "✓ Admin user setup complete"
}

# Setup firewall
setup_firewall() {
    print_color "$YELLOW" "Configuring firewall..."
    
    if command -v ufw; then
        # UFW firewall
        ufw allow 8000/tcp
        ufw --force enable
        print_color "$GREEN" "✓ UFW firewall configured"
    elif command -v firewall-cmd; then
        # Firewalld
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --reload
        print_color "$GREEN" "✓ Firewalld configured"
    else
        print_color "$YELLOW" "⚠ Please manually open port 8000 in your firewall"
    fi
}

# Start services
start_services() {
    print_color "$YELLOW" "Starting Marzban services..."
    
    # Start Marzban service
    systemctl start ${SERVICE_NAME}
    systemctl status ${SERVICE_NAME}
    
    print_color "$GREEN" "✓ Marzban service started"
}

# Show installation summary
show_summary() {
    print_color "$GREEN" "╔══════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    print_color "$GREEN" "║${NC}                        ${GREEN}Installation Complete!${NC}                        ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} Marzban with Advanced Limits System has been successfully installed! ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                                       ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} Web Interface: ${BLUE}http://$(hostname -I | awk '{print $1}'):8000${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} Installation Directory: ${BLUE}${INSTALL_DIR}${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} Configuration File: ${BLUE}${INSTALL_DIR}/.env${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} Service Status: ${BLUE}systemctl status ${SERVICE_NAME}${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                                       ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC} Next Steps: ${YELLOW}1. Edit .env file with your settings${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}              ${YELLOW}2. Access web interface to configure limits${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}              ${YELLOW}3. Create users and apply templates${NC} ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_color "$BLUE" "🚀 Marzban with Advanced Limits is ready to use!"
    print_color "$YELLOW" "📋 Features: Limits Management | Templates | Monitoring | Notifications"
}

# Uninstall function
uninstall() {
    print_color "$RED" "Uninstalling Marzban..."
    
    # Stop service
    systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    systemctl disable ${SERVICE_NAME} 2>/dev/null || true
    
    # Remove files
    rm -rf $INSTALL_DIR
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    rm -f /etc/logrotate.d/marzban
    
    # Reload systemd
    systemctl daemon-reload
    
    print_color "$GREEN" "✓ Marzban uninstalled"
}

# Update function
update() {
    print_color "$YELLOW" "Updating Marzban..."
    
    cd $INSTALL_DIR
    source venv/bin/activate
    
    # Backup current database
    cp /var/lib/marzban/app.db /var/lib/marzban/app.db.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # Download latest version
    curl -L -o ${SCRIPT_NAME}.new \
        "https://github.com/${REPO_OWNER}/${REPO_NAME}/raw/master/${SCRIPT_NAME}"
    
    # Update requirements if needed
    curl -L -o requirements.txt.new \
        "https://github.com/${REPO_OWNER}/${REPO_NAME}/raw/master/requirements.txt"
    
    # Install updates
    if [[ -f "${SCRIPT_NAME}.new" ]]; then
        mv ${SCRIPT_NAME}.new ${SCRIPT_NAME}
        pip install -r requirements.txt.new
        rm requirements.txt.new
    fi
    
    # Run migrations
    alembic upgrade head
    
    # Restart service
    systemctl restart ${SERVICE_NAME}
    
    print_color "$GREEN" "✓ Marzban updated successfully"
}

# Show help
show_help() {
    echo "Marzban Installation Script with Advanced Limits System"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install    - Install Marzban with limits system"
    echo "  update     - Update existing installation"
    echo "  uninstall  - Uninstall Marzban"
    echo "  status     - Show service status"
    echo "  logs       - Show service logs"
    echo "  restart    - Restart Marzban service"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo bash $0 install"
    echo "  sudo bash $0 update"
    echo "  sudo bash $0 status"
}

# Main execution
main() {
    print_header
    
    case "${1:-install}" in
        install)
            check_root
            detect_os
            install_dependencies
            create_install_dir
            download_marzban
            setup_python_env
            setup_database
            create_service
            setup_config
            setup_logrotate
            create_admin
            setup_firewall
            start_services
            show_summary
            ;;
        update)
            check_root
            update
            ;;
        uninstall)
            check_root
            uninstall
            ;;
        status)
            systemctl status ${SERVICE_NAME}
            ;;
        logs)
            journalctl -u ${SERVICE_NAME} -f
            ;;
        restart)
            systemctl restart ${SERVICE_NAME}
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_color "$RED" "Error: Unknown command '$1'"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
