"""Pytest fixtures for vulnerability pattern tests."""

import pytest
from tests.sdk_helpers import KVStore


@pytest.fixture
def store() -> KVStore:
    return KVStore()
