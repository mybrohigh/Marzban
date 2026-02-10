#!/bin/bash

# Xray-core installation script for Marzban
# This script downloads and installs the latest Xray-core

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to detect architecture
detect_arch() {
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="64"
            ;;
        aarch64)
            ARCH="arm64-v8a"
            ;;
        armv7l)
            ARCH="arm32-v7a"
            ;;
        *)
            print_color $RED "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
}

# Function to download and install Xray-core
install_xray() {
    local version=$1
    local xray_filename="Xray-linux-${ARCH}.zip"
    local download_url="https://github.com/XTLS/Xray-core/releases/download/${version}/${xray_filename}"
    
    print_color $BLUE "Downloading Xray-core ${version} for ${ARCH}..."
    
    # Download Xray-core
    if ! curl -L -o "${xray_filename}" "${download_url}"; then
        print_color $RED "Failed to download Xray-core"
        exit 1
    fi
    
    print_color $BLUE "Extracting Xray-core..."
    
    # Extract Xray-core
    if ! unzip -o "${xray_filename}"; then
        print_color $RED "Failed to extract Xray-core"
        rm -f "${xray_filename}"
        exit 1
    fi
    
    rm -f "${xray_filename}"
    
    # Install Xray-core
    chmod +x xray
    mv xray /usr/local/bin/
    
    print_color $GREEN "Xray-core ${version} installed successfully!"
}

# Main script logic
main() {
    print_color $BLUE "Xray-core Installation Script"
    print_color $YELLOW "================================="
    
    detect_arch
    
    # Get latest version if no version specified
    if [ -z "$1" ]; then
        VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep -oP '"tag_name": "\K[^"]*')
    else
        VERSION="$1"
    fi
    
    if [ -z "$VERSION" ]; then
        print_color $RED "Failed to get latest version"
        exit 1
    fi
    
    install_xray "$VERSION"
}

# Run main function
main "$@"
