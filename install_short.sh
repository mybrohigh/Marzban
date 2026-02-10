#!/bin/bash

# Short installation script for Marzban with limits
# Solves "Argument list too long" error

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing Marzban with Advanced Limits System...${NC}"

# Download and install
curl -sL https://github.com/mybrohigh/Marzban/raw/master/install_marzban_with_limits.sh | bash

echo -e "${GREEN}✓ Marzban with limits installed successfully!${NC}"
echo -e "${BLUE}Web Interface: http://$(hostname -I | awk '{print $1}'):8000${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "${YELLOW}1. Edit /opt/marzban/.env with your settings${NC}"
echo -e "${YELLOW}2. Access web interface to configure limits${NC}"
