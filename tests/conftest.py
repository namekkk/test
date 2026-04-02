# tests/conftest.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from logging_config import setup_logging
from api_client import login

setup_logging()

@pytest.fixture(scope="session")
def token():
    return login("admin", "Qaz123456")