#!/bin/bash
# =============================================================================
# Cuscli Offline Deployment - Install Script (Linux)
# Description: Install cuscli in offline/intranet environment
# Creates virtual environment and installs all dependencies from local packages
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

# Configuration
VENV_DIR="${SCRIPT_DIR}/venv"
PACKAGES_DIR="${SCRIPT_DIR}/packages/linux_x86_64"
WHEELS_DIR="${SCRIPT_DIR}/wheels"
PYTHON_CMD="${PYTHON_CMD:-python3}"

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Cuscli Offline Installation${NC}"
    echo -e "${BLUE}  Linux x86_64${NC}"
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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_system() {
    print_info "Checking system requirements..."

    # Check architecture
    local arch=$(uname -m)
    if [[ "$arch" != "x86_64" ]]; then
        print_error "Unsupported architecture: $arch"
        print_error "This script only supports x86_64"
        exit 1
    fi
    print_info "Architecture: $arch"

    # Check Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        print_error "Python3 is not installed"
        print_error "Please install Python 3.10 or later"
        exit 1
    fi

    local py_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local py_major=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
    local py_minor=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

    if [[ "$py_major" -lt 3 ]] || [[ "$py_major" -eq 3 && "$py_minor" -lt 10 ]]; then
        print_error "Python version too old: $py_version"
        print_error "Requires Python 3.10 or later"
        exit 1
    fi
    print_info "Python version: $py_version"

    # Check packages directory
    if [[ ! -d "$PACKAGES_DIR" ]]; then
        print_error "Packages directory not found: $PACKAGES_DIR"
        print_error "Please run download_deps.sh first on a machine with internet access"
        exit 1
    fi

    local pkg_count=$(find "$PACKAGES_DIR" -name "*.whl" -o -name "*.tar.gz" 2>/dev/null | wc -l)
    if [[ "$pkg_count" -eq 0 ]]; then
        print_error "No packages found in $PACKAGES_DIR"
        print_error "Please run download_deps.sh first"
        exit 1
    fi
    print_info "Found $pkg_count packages"

    # Check wheel file
    local wheel_file=$(find "$WHEELS_DIR" -name "*.whl" -type f 2>/dev/null | head -n1)
    if [[ -z "$wheel_file" ]]; then
        print_warn "No cuscli wheel file found in $WHEELS_DIR"
        print_warn "Will install dependencies only"
    else
        print_info "Wheel file: $(basename "$wheel_file")"
    fi

    print_info "System check passed"
}

create_venv() {
    print_info "Creating virtual environment..."

    if [[ -d "$VENV_DIR" ]]; then
        print_warn "Virtual environment already exists: $VENV_DIR"
        read -p "Do you want to recreate it? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        else
            print_info "Using existing virtual environment"
            return 0
        fi
    fi

    $PYTHON_CMD -m venv "$VENV_DIR"
    print_info "Virtual environment created: $VENV_DIR"
}

upgrade_pip() {
    print_info "Upgrading pip in virtual environment..."

    source "$VENV_DIR/bin/activate"

    # Try to upgrade pip from local packages first
    local pip_wheel=$(find "$PACKAGES_DIR" -name "pip-*.whl" -type f 2>/dev/null | sort -V | tail -n1)
    if [[ -n "$pip_wheel" ]]; then
        pip install --no-index --find-links="$PACKAGES_DIR" pip --upgrade --quiet
        print_info "pip upgraded from local package"
    else
        print_warn "pip wheel not found, using bundled pip"
    fi
}

install_dependencies() {
    print_info "Installing dependencies from local packages..."

    source "$VENV_DIR/bin/activate"

    # Install all packages from local directory
    pip install --no-index --find-links="$PACKAGES_DIR" \
        --find-links="$WHEELS_DIR" \
        wheel setuptools \
        2>&1 | grep -v "already satisfied" || true

    # Install all dependencies
    print_info "Installing all dependencies (this may take a while)..."
    pip install --no-index --find-links="$PACKAGES_DIR" \
        --find-links="$WHEELS_DIR" \
        -r "${SCRIPT_DIR}/../requirements.txt" \
        2>&1 | while read line; do
            if [[ "$line" == *"Successfully installed"* ]]; then
                echo -e "  ${GREEN}>${NC} $line"
            elif [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"error"* ]]; then
                echo -e "  ${RED}>${NC} $line"
            fi
        done

    print_info "Dependencies installed"
}

install_cuscli() {
    print_info "Installing cuscli..."

    source "$VENV_DIR/bin/activate"

    local wheel_file=$(find "$WHEELS_DIR" -name "*.whl" -type f 2>/dev/null | sort -V | tail -n1)
    if [[ -n "$wheel_file" ]]; then
        pip install --no-index --find-links="$PACKAGES_DIR" "$wheel_file" --force-reinstall
        print_info "Cuscli installed: $(basename "$wheel_file")"
    else
        print_warn "No cuscli wheel file found, skipping installation"
    fi
}

verify_installation() {
    print_info "Verifying installation..."

    source "$VENV_DIR/bin/activate"

    # Check if cuscli is installed
    if pip show cuscli &> /dev/null || pip show auto-coder &> /dev/null; then
        local version=$(pip show cuscli 2>/dev/null | grep "^Version:" | cut -d' ' -f2 || pip show auto-coder 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
        print_success "Cuscli version: ${version:-unknown}"
    fi

    # Try to import the module
    if $PYTHON_CMD -c "from autocoder import chat_auto_coder" 2>/dev/null; then
        print_success "Module import: OK"
    else
        print_warn "Module import failed (may need additional configuration)"
    fi

    # Check entry points
    if command -v cuscli &> /dev/null; then
        print_success "Entry point 'cuscli': OK"
    elif [[ -f "$VENV_DIR/bin/cuscli" ]]; then
        print_success "Entry point 'cuscli': OK (in venv)"
    else
        print_warn "Entry point 'cuscli' not found"
    fi
}

show_completion() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Installation Complete!${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${GREEN}Virtual environment:${NC} $VENV_DIR"
    echo ""
    echo -e "${GREEN}To use cuscli:${NC}"
    echo ""
    echo "  Option 1 - Use the start script:"
    echo "    ./start.sh"
    echo ""
    echo "  Option 2 - Manually activate the virtual environment:"
    echo "    source $VENV_DIR/bin/activate"
    echo "    cuscli"
    echo ""
    echo "  Option 3 - Run directly without activation:"
    echo "    $VENV_DIR/bin/cuscli"
    echo ""
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --python CMD   Specify Python command (default: python3)"
    echo "  -y, --yes          Auto-confirm all prompts"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Install with default settings"
    echo "  $0 -p python3.10   # Use specific Python version"
    echo "  $0 -y              # Non-interactive mode"
}

# Parse arguments
AUTO_CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        -y|--yes)
            AUTO_CONFIRM=true
            shift
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
check_system
create_venv
upgrade_pip
install_dependencies
install_cuscli
verify_installation
show_completion

print_success "Installation completed successfully!"
