"""
Test configuration for Gateway integration tests.

This module contains configuration settings and constants used in the integration tests.
"""
import os
from typing import Dict, Any

# Test environment configuration
TEST_ENV = os.environ.get("TEST_ENV", "local")

# Base URLs for services
GATEWAY_BASE_URL = os.environ.get(
    "GATEWAY_BASE_URL", 
    "http://localhost:8000"
)

# Test user credentials
TEST_USER = {
    "username": os.environ.get("TEST_USERNAME", "testuser"),
    "password": os.environ.get("TEST_PASSWORD", "testpass"),
    "email": os.environ.get("TEST_EMAIL", "test@example.com")
}

# API version
API_VERSION = "v1"

# API endpoints
ENDPOINTS = {
    "auth": {
        "token": "/api/v1/auth/token",
        "refresh": "/api/v1/auth/refresh",
        "user_info": "/api/v1/auth/me"
    },
    "datanodes": {
        "base": "/api/v1/datanodes",
        "by_id": "/api/v1/datanodes/{datanode_id}",
        "query": "/api/v1/datanodes/query"
    },
    "strategies": {
        "base": "/api/v1/strategies",
        "by_id": "/api/v1/strategies/{strategy_id}",
        "deploy": "/api/v1/strategies/{strategy_id}/deploy",
        "status": "/api/v1/strategies/{strategy_id}/status"
    },
    "pipelines": {
        "base": "/api/v1/pipelines",
        "by_id": "/api/v1/pipelines/{pipeline_id}",
        "execute": "/api/v1/pipelines/{pipeline_id}/execute"
    }
}

# Test timeouts (in seconds)
TIMEOUTS = {
    "short": 5,
    "medium": 15,
    "long": 30,
    "very_long": 60
}

# Test tags for categorizing tests
TEST_TAGS = {
    "smoke": "Basic functionality tests",
    "integration": "Integration between components",
    "e2e": "End-to-end workflow tests",
    "auth": "Authentication and authorization tests",
    "performance": "Performance and load testing"
}

# Default request headers
DEFAULT_HEADERS = {
    "Content-Type": "application/x-protobuf",
    "Accept": "application/x-protobuf"
}

# Test data directory
TEST_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "test_data"
)

def get_endpoint(service: str, endpoint: str, **kwargs) -> str:
    """
    Get the full URL for an API endpoint.
    
    Args:
        service: The service name (e.g., 'auth', 'datanodes')
        endpoint: The endpoint name (e.g., 'token', 'by_id')
        **kwargs: Format string arguments for the endpoint
        
    Returns:
        str: The full URL for the endpoint
    """
    if service not in ENDPOINTS:
        raise ValueError(f"Unknown service: {service}")
    if endpoint not in ENDPOINTS[service]:
        raise ValueError(f"Unknown endpoint '{endpoint}' for service '{service}'")
    
    path = ENDPOINTS[service][endpoint].format(**kwargs)
    return f"{GATEWAY_BASE_URL.rstrip('/')}{path}"
