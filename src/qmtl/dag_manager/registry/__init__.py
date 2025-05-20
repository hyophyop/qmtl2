"""
Registry service package for managing node and strategy metadata.

This package provides services for managing nodes, strategies, and their relationships
in the QMTL system using Neo4j as the backend store.
"""

# Import key components for easier access
from .registry_client import RegistryClient

__all__ = ['RegistryClient']
