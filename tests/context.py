from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

auth_headers = {
    "Authorization" : "test"
}