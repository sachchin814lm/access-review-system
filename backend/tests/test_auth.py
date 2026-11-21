"""Tests for authentication endpoints."""


class TestLogin:
    def test_login_success(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'alice', 'password': 'password123'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data
        assert data['user']['username'] == 'alice'
        assert data['user']['role'] == 'employee'

    def test_login_wrong_password(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'alice', 'password': 'wrongpassword'
        })
        assert resp.status_code == 401
        assert 'error' in resp.get_json()

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'nonexistent', 'password': 'password123'
        })
        assert resp.status_code == 401

    def test_login_missing_username(self, client):
        resp = client.post('/api/auth/login', json={'password': 'password123'})
        assert resp.status_code == 400

    def test_login_missing_password(self, client):
        resp = client.post('/api/auth/login', json={'username': 'alice'})
        assert resp.status_code == 400

    def test_login_empty_body(self, client):
        resp = client.post('/api/auth/login',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_login_all_demo_accounts(self, client):
        """Every seeded user can log in."""
        users = ['alice', 'bob', 'charlie', 'diana', 'eve',
                 'frank', 'grace', 'heidi', 'ivan', 'judy']
        for username in users:
            resp = client.post('/api/auth/login', json={
                'username': username, 'password': 'password123'
            })
            assert resp.status_code == 200, f'Login failed for {username}'


class TestMe:
    def test_me_authenticated(self, client, auth_headers):
        headers = auth_headers('alice')
        resp = client.get('/api/auth/me', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['user']['username'] == 'alice'

    def test_me_unauthenticated(self, client):
        resp = client.get('/api/auth/me')
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalidtoken123'
        })
        assert resp.status_code == 401

    def test_me_returns_role(self, client, auth_headers):
        headers = auth_headers('grace')
        resp = client.get('/api/auth/me', headers=headers)
        assert resp.get_json()['user']['role'] == 'it_admin'


class TestLogout:
    def test_logout_invalidates_token(self, client, auth_headers):
        headers = auth_headers('alice')
        # Confirm we are logged in
        assert client.get('/api/auth/me', headers=headers).status_code == 200
        # Log out
        resp = client.post('/api/auth/logout', headers=headers)
        assert resp.status_code == 200
        # Token should be invalid now
        assert client.get('/api/auth/me', headers=headers).status_code == 401

    def test_logout_requires_auth(self, client):
        resp = client.post('/api/auth/logout')
        assert resp.status_code == 401
