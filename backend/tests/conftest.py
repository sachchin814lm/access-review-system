import pytest
from app import create_app, db as _db
from app.config import TestConfig
from app.seed import seed


@pytest.fixture()
def app():
    """Create a fresh app with a seeded in-memory database for each test."""
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        seed()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    """Factory fixture: returns Authorization headers for a given username."""
    def _get_headers(username='alice', password='password123'):
        response = client.post('/api/auth/login', json={
            'username': username,
            'password': password,
        })
        data = response.get_json()
        return {'Authorization': f'Bearer {data["token"]}'}
    return _get_headers
