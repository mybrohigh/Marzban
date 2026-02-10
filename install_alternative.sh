#!/bin/bash

# Alternative installation method that bypasses curl issues
# Downloads script using wget instead of curl

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing Marzban with Advanced Limits System (Alternative Method)...${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root!"
    echo "Please use: sudo bash $0"
    exit 1
fi

# Download using wget (more reliable than curl in some cases)
echo -e "${BLUE}Downloading installation script using wget...${NC}"
if wget -q -O install_marzban_with_limits.sh \
    "https://raw.githubusercontent.com/mybrohigh/Marzban/master/install_marzban_with_limits.sh"; then
    echo -e "${GREEN}✓ Script downloaded successfully${NC}"
else
    echo -e "${RED}✗ Failed to download script${NC}"
    echo -e "${YELLOW}Trying alternative method...${NC}"
    
    # Fallback: create minimal installation command
    cat > install_marzban_with_limits.sh << 'EOF'
#!/bin/bash
set -e
INSTALL_DIR="/opt"
APP_NAME="marzban"
INSTALL_MODE="native"

# Auto-detect native mode (no Docker)
INSTALL_MODE="native"

echo "Installing Marzban with limits..."
# Download main files
wget -q -O marzban.sh "https://raw.githubusercontent.com/mybrohigh/Marzban/master/marzban.sh"
wget -q -O requirements.txt "https://raw.githubusercontent.com/mybrohigh/Marzban/master/requirements.txt"

# Make executable
chmod +x marzban.sh

# Install system dependencies
apt update > /dev/null 2>&1
apt install -y python3 python3-pip python3-venv sqlite3 systemd > /dev/null 2>&1

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install additional dependencies
pip install aiohttp sqlalchemy alembic

# Create directories
mkdir -p /var/lib/marzban
mkdir -p /opt/marzban

# Setup database
export SQLALCHEMY_DATABASE_URL="sqlite:///var/lib/marzban/app.db"
alembic upgrade head

# Create systemd service
cat > /etc/systemd/system/marzban.service << 'EOF'
[Unit]
Description=Marzban with Advanced Limits
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/marzban
Environment=PATH=/opt/marzban/venv/bin
Environment=SQLALCHEMY_DATABASE_URL=sqlite:///var/lib/marzban/app.db
ExecStart=/opt/marzban/venv/bin/python /opt/marzban/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable marzban

# Create configuration file
cat > /opt/marzban/.env << 'EOF'
SQLALCHEMY_DATABASE_URL=sqlite:///var/lib/marzban/app.db
DEBUG=false
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
EOF

# Start service
systemctl start marzban

echo "✓ Marzban with limits installed!"
echo "Web Interface: http://$(hostname -I | awk '{print $1}'):8000"
EOF

    chmod +x install_marzban_with_limits.sh
    
    echo -e "${GREEN}✓ Alternative installation script created${NC}"
fi

# Execute the installation
if [[ -f install_marzban_with_limits.sh ]]; then
    echo -e "${BLUE}Running installation...${NC}"
    bash install_marzban_with_limits.sh
else
    echo -e "${RED}✗ Installation script not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Marzban with Advanced Limits System installed successfully!${NC}"
echo -e "${BLUE}Web Interface: http://$(hostname -I | awk '{print $1}'):8000${NC}"
echo -e "${YELLOW}Configuration: /opt/marzban/.env${NC}"
