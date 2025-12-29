#!/bin/bash
# =============================================================================
# Cuscli Startup Script (Linux)
# Description: Activate virtual environment and start cuscli
# Usage: Run this script from your project directory
# =============================================================================

# Script directory (where deploy is installed)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

# Current working directory (user's project directory)
WORK_DIR="$(pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found: $VENV_DIR"
    echo -e "${RED}[ERROR]${NC} Please run install_offline.sh first"
    exit 1
fi

# Check if activate script exists
if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment is corrupted"
    echo -e "${RED}[ERROR]${NC} Please re-run install_offline.sh"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set environment variables for Chinese language support
export LANG="${LANG:-zh_CN.UTF-8}"
export LC_ALL="${LC_ALL:-zh_CN.UTF-8}"

# Print startup info
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Cuscli AI Programming Assistant${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${GREEN}Virtual environment:${NC} $VENV_DIR"
echo -e "${GREEN}Python:${NC} $(python --version 2>&1)"
echo ""
echo -e "${GREEN}Working directory:${NC} $WORK_DIR"
echo ""

# Check if we're in the deploy directory
if [[ "$WORK_DIR" == "$SCRIPT_DIR" ]]; then
    echo -e "${YELLOW}[WARN]${NC} You are running from the deploy directory."
    echo -e "${YELLOW}[WARN]${NC} Please run this script from your project directory."
    echo ""
    echo "Usage:"
    echo "  1. cd to your project directory"
    echo "  2. Run: $SCRIPT_DIR/start.sh"
    echo ""
    read -p "Enter project directory path (or press Enter to continue anyway): " PROJECT_DIR
    if [[ -n "$PROJECT_DIR" ]]; then
        if [[ -d "$PROJECT_DIR" ]]; then
            cd "$PROJECT_DIR"
            WORK_DIR="$PROJECT_DIR"
            echo ""
            echo -e "Changed to: $PROJECT_DIR"
            echo ""
        else
            echo -e "${RED}[ERROR]${NC} Directory not found: $PROJECT_DIR"
            exit 1
        fi
    fi
fi

# Start cuscli with all passed arguments
if [[ $# -eq 0 ]]; then
    # No arguments - start interactive chat mode
    exec cuscli
else
    # Pass all arguments to cuscli
    exec cuscli "$@"
fi
