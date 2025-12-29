#!/bin/bash
# =============================================================================
# Cuscli Offline Deployment - Download Dependencies Script (Linux)
# Description: Download Linux x86_64 dependencies for offline installation
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
PACKAGES_DIR="${SCRIPT_DIR}/packages/linux_x86_64"
WHEELS_DIR="${SCRIPT_DIR}/wheels"

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Cuscli Offline Deployment (Linux)${NC}"
    echo -e "${BLUE}  Download Dependencies Script${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_info "Checking requirements..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        exit 1
    fi

    PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_info "Python version: ${PYTHON_VER}"

    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not installed"
        exit 1
    fi

    # Check requirements.txt
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "requirements.txt not found: $REQUIREMENTS_FILE"
        exit 1
    fi

    print_info "All requirements satisfied"
}

download_packages() {
    print_info "Downloading Linux x86_64 packages..."

    mkdir -p "$PACKAGES_DIR"

    # Download essential build tools first (pip, wheel, setuptools)
    print_info "Downloading essential build tools..."
    python3 -m pip download \
        pip wheel setuptools \
        -d "$PACKAGES_DIR" \
        --python-version "$PYTHON_VERSION" \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        2>&1 | grep -E "(Downloading|Using cached)" | while read line; do
            echo -e "  ${GREEN}>${NC} $line"
        done || true

    # Download for current platform (Linux x86_64)
    print_info "Downloading dependencies..."
    python3 -m pip download \
        -r "$REQUIREMENTS_FILE" \
        -d "$PACKAGES_DIR" \
        --python-version "$PYTHON_VERSION" \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        2>&1 | while read line; do
            if [[ "$line" == *"Downloading"* ]] || [[ "$line" == *"Using cached"* ]]; then
                echo -e "  ${GREEN}>${NC} $line"
            fi
        done || true

    # Also download source distributions for packages without wheels
    print_info "Downloading source packages (fallback)..."
    python3 -m pip download \
        -r "$REQUIREMENTS_FILE" \
        -d "$PACKAGES_DIR" \
        --no-binary=:none: \
        2>&1 | grep -E "(Downloading|Using cached|already downloaded)" | while read line; do
            echo -e "  ${GREEN}>${NC} $line"
        done || true

    local count=$(find "$PACKAGES_DIR" -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" 2>/dev/null | wc -l)
    print_info "Downloaded ${count} packages to ${PACKAGES_DIR}"
}

copy_wheel() {
    print_info "Copying cuscli wheel package..."

    mkdir -p "$WHEELS_DIR"

    # Find the latest wheel in dist directory
    local wheel_file=$(find "${PROJECT_ROOT}/dist" -name "*.whl" -type f 2>/dev/null | sort -V | tail -n1)

    if [[ -n "$wheel_file" && -f "$wheel_file" ]]; then
        cp "$wheel_file" "$WHEELS_DIR/"
        print_info "Copied: $(basename "$wheel_file")"
    else
        print_warn "No wheel file found in ${PROJECT_ROOT}/dist"
        print_warn "Please build the wheel first: cd ${PROJECT_ROOT} && ./scripts/build_wheel.sh"
    fi
}

show_summary() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Download Summary${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""

    echo -e "${GREEN}Packages:${NC}"
    local pkg_count=$(find "$PACKAGES_DIR" -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" 2>/dev/null | wc -l)
    local pkg_size=$(du -sh "$PACKAGES_DIR" 2>/dev/null | cut -f1)
    echo "  Location: $PACKAGES_DIR"
    echo "  Count: ${pkg_count}"
    echo "  Size: ${pkg_size:-0}"
    echo ""

    echo -e "${GREEN}Wheel package:${NC}"
    local wheel_file=$(find "$WHEELS_DIR" -name "*.whl" -type f 2>/dev/null | head -n1)
    if [[ -n "$wheel_file" ]]; then
        echo "  Location: $WHEELS_DIR"
        echo "  File: $(basename "$wheel_file")"
    else
        echo "  Status: Not found (need to build first)"
    fi
    echo ""

    echo -e "${GREEN}Next steps:${NC}"
    echo "  1. Package: zip -r cuscli-linux.zip deploy/"
    echo "  2. Transfer to target machine"
    echo "  3. Run: ./install_offline.sh"
    echo ""
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --python VER     Specify Python version (default: 3.10)"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                   # Download with default settings"
    echo "  $0 -p 3.11           # Download for Python 3.11"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main
print_header
check_requirements
download_packages
copy_wheel
show_summary

print_info "Download completed successfully!"
