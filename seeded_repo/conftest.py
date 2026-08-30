import sys
import os
import pytest

# Ensure seeded_repo/src is in sys.path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

@pytest.fixture(scope="session")
def global_app_context():
    """Session-level fixture context."""
    return {"version": "2.4.0", "env": "test"}
