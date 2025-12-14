#!/bin/bash
# Server Diagnostics Script
# Run this script on the target server to check deployment readiness

set -e

echo "=========================================="
echo "Server Deployment Diagnostics"
echo "=========================================="
echo ""

# OS Information
echo "=== Operating System ==="
if [ -f /etc/os-release ]; then
    cat /etc/os-release | grep -E "^(NAME|VERSION)="
elif [ -f /etc/redhat-release ]; then
    cat /etc/redhat-release
else
    echo "Unknown OS"
fi
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Hostname: $(hostname)"
echo ""

# System Resources
echo "=== System Resources ==="
echo "Disk Space:"
df -h / | tail -1
echo ""
echo "Memory:"
free -h | grep Mem
echo ""
echo "CPU Cores: $(nproc)"
echo ""

# Docker
echo "=== Docker ==="
if command -v docker &> /dev/null; then
    echo "✓ Docker installed: $(docker --version)"
    if docker info &> /dev/null; then
        echo "✓ Docker daemon is running"
        echo "  Docker version: $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo 'unknown')"
    else
        echo "✗ Docker daemon is not running or not accessible"
    fi
else
    echo "✗ Docker not installed"
fi
echo ""

# Python
echo "=== Python ==="
if command -v python3 &> /dev/null; then
    echo "✓ Python 3: $(python3 --version)"
    echo "  Path: $(which python3)"
else
    echo "✗ Python 3 not found"
fi
echo ""

# Node.js
echo "=== Node.js ==="
if command -v node &> /dev/null; then
    echo "✓ Node.js: $(node --version)"
    echo "  npm: $(npm --version 2>/dev/null || echo 'not found')"
    echo "  Path: $(which node)"
else
    echo "⚠ Node.js not found (will be installed during deployment)"
fi
echo ""

# Git
echo "=== Git ==="
if command -v git &> /dev/null; then
    echo "✓ Git: $(git --version)"
else
    echo "✗ Git not found"
fi
echo ""

# Ports
echo "=== Port Availability ==="
PORTS=(5432 6333 8000 8001 8080)
for port in "${PORTS[@]}"; do
    if nc -z localhost $port 2>/dev/null || ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo "✗ Port $port is in use"
    else
        echo "✓ Port $port is available"
    fi
done
echo ""

# Permissions
echo "=== User Permissions ==="
echo "Current user: $(whoami)"
if sudo -n true 2>/dev/null; then
    echo "✓ User has sudo access (passwordless)"
elif sudo -v 2>/dev/null; then
    echo "⚠ User has sudo access (requires password)"
else
    echo "✗ User does not have sudo access"
fi

if groups | grep -q docker; then
    echo "✓ User is in docker group"
else
    echo "⚠ User is not in docker group"
fi

if [ -w /opt ]; then
    echo "✓ User can write to /opt"
else
    echo "⚠ User cannot write to /opt (may need sudo)"
fi
echo ""

# Network
echo "=== Network ==="
echo "IP Addresses:"
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -5
echo ""

# Summary
echo "=========================================="
echo "Diagnostics Complete"
echo "=========================================="

