import os
import tempfile

# Must be set before the app is imported
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["SLOW_THRESHOLD_SECONDS"] = "0.2"

import pytest
from fastapi.testclient import TestClient

from app import ratelimit
from app.main import app


@pytest.fixture()
def client():
    ratelimit.reset()
    return TestClient(app)


HEADERS = {"X-API-Key": "demo-valid-key"}
