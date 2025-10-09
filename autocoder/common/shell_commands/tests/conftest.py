"""
Pytest configuration for Shell Commands module tests.

This file provides pytest configuration including fixtures, markers,
and test collection rules for the shell commands test suite.
"""

import pytest
import platform
import tempfile
import shutil
from typing import Generator

# Define custom pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests (may be slower)"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks tests as performance tests (may be slow and resource intensive)"
    )
    config.addinivalue_line(
        "markers",
        "platform_specific: marks tests that are specific to certain platforms"
    )
    config.addinivalue_line(
        "markers",
        "requires_pexpect: marks tests that require pexpect to be available"
    )


@pytest.fixture
def temp_directory() -> Generator[str, None, None]:
    """Provide a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@pytest.fixture  
def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


@pytest.fixture
def is_unix() -> bool:
    """Check if running on Unix-like system."""
    return platform.system() in ("Linux", "Darwin")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add skip conditions."""
    # Skip performance tests by default unless explicitly requested
    if not config.getoption("--run-performance"):
        skip_performance = pytest.mark.skip(reason="Performance tests skipped (use --run-performance to enable)")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_performance)
                
    # Skip integration tests if requested
    if config.getoption("--skip-integration"):
        skip_integration = pytest.mark.skip(reason="Integration tests skipped")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance tests (disabled by default)"
    )
    parser.addoption(
        "--skip-integration", 
        action="store_true",
        default=False,
        help="Skip integration tests"
    )
    parser.addoption(
        "--test-timeout",
        type=int,
        default=30,
        help="Default timeout for individual tests in seconds"
    )


# Pytest hooks for better test organization
def pytest_runtest_setup(item):
    """Setup hook called before each test."""
    # Set timeout for long-running tests
    if hasattr(item, 'get_closest_marker'):
        performance_marker = item.get_closest_marker("performance")
        integration_marker = item.get_closest_marker("integration")
        
        if performance_marker:
            # Performance tests get longer timeout
            if not hasattr(item, '_timeout'):
                item._timeout = 120  # 2 minutes for performance tests
        elif integration_marker:
            # Integration tests get moderate timeout
            if not hasattr(item, '_timeout'):
                item._timeout = 60   # 1 minute for integration tests
        else:
            # Unit tests get standard timeout
            if not hasattr(item, '_timeout'):
                item._timeout = 30   # 30 seconds for unit tests
