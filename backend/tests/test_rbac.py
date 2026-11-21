"""Tests for role-based access control on user and application routes."""


class TestUserRoutePermissions:
    """User management is restricted to IT Admin (full) and Auditor (read-only)."""

    def test_employee_cannot_list_users(self, client, auth_headers):
        resp = client.get('/api/users', headers=auth_headers('alice'))
        assert resp.status_code == 403

    def test_manager_cannot_list_users(self, client, auth_headers):
        resp = client.get('/api/users', headers=auth_headers('charlie'))
        assert resp.status_code == 403

    def test_app_owner_cannot_list_users(self, client, auth_headers):
        resp = client.get('/api/users', headers=auth_headers('eve'))
        assert resp.status_code == 403

    def test_it_admin_can_list_users(self, client, auth_headers):
        resp = client.get('/api/users', headers=auth_headers('grace'))
        assert resp.status_code == 200
        assert len(resp.get_json()['users']) >= 10

    def test_auditor_can_list_users(self, client, auth_headers):
        resp = client.get('/api/users', headers=auth_headers('ivan'))
        assert resp.status_code == 200

    def test_auditor_cannot_create_user(self, client, auth_headers):
        resp = client.post('/api/users', headers=auth_headers('ivan'), json={
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'pass123', 'full_name': 'New User', 'role': 'employee',
        })
        assert resp.status_code == 403

    def test_it_admin_can_create_user(self, client, auth_headers):
        resp = client.post('/api/users', headers=auth_headers('grace'), json={
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'pass123', 'full_name': 'New User', 'role': 'employee',
        })
        assert resp.status_code == 201
        assert resp.get_json()['user']['username'] == 'newuser'

    def test_employee_cannot_update_user(self, client, auth_headers):
        resp = client.put('/api/users/1', headers=auth_headers('alice'),
                          json={'full_name': 'Hacked'})
        assert resp.status_code == 403

    def test_employee_cannot_delete_user(self, client, auth_headers):
        resp = client.delete('/api/users/1', headers=auth_headers('alice'))
        assert resp.status_code == 403

    def test_it_admin_can_update_user(self, client, auth_headers):
        headers = auth_headers('grace')
        users = client.get('/api/users', headers=headers).get_json()['users']
        uid = users[0]['id']
        resp = client.put(f'/api/users/{uid}', headers=headers,
                          json={'full_name': 'Updated Name'})
        assert resp.status_code == 200
        assert resp.get_json()['user']['full_name'] == 'Updated Name'

    def test_it_admin_can_deactivate_user(self, client, auth_headers):
        headers = auth_headers('grace')
        users = client.get('/api/users', headers=headers).get_json()['users']
        uid = users[-1]['id']
        resp = client.delete(f'/api/users/{uid}', headers=headers)
        assert resp.status_code == 200

    def test_create_user_duplicate_username(self, client, auth_headers):
        resp = client.post('/api/users', headers=auth_headers('grace'), json={
            'username': 'alice', 'email': 'dup@example.com',
            'password': 'pass', 'full_name': 'Dup', 'role': 'employee',
        })
        assert resp.status_code == 409

    def test_create_user_invalid_role(self, client, auth_headers):
        resp = client.post('/api/users', headers=auth_headers('grace'), json={
            'username': 'badrole', 'email': 'br@example.com',
            'password': 'pass', 'full_name': 'Bad', 'role': 'superadmin',
        })
        assert resp.status_code == 400


class TestApplicationRoutePermissions:
    """Application listing is open; management is IT Admin only."""

    def test_any_authenticated_user_can_list_apps(self, client, auth_headers):
        for username in ['alice', 'charlie', 'eve', 'grace', 'ivan']:
            resp = client.get('/api/applications', headers=auth_headers(username))
            assert resp.status_code == 200, f'{username} should list apps'

    def test_unauthenticated_cannot_list_apps(self, client):
        assert client.get('/api/applications').status_code == 401

    def test_employee_cannot_create_app(self, client, auth_headers):
        resp = client.post('/api/applications', headers=auth_headers('alice'), json={
            'name': 'ForbiddenApp', 'owner_id': 1, 'access_levels': ['Read'],
        })
        assert resp.status_code == 403

    def test_manager_cannot_create_app(self, client, auth_headers):
        resp = client.post('/api/applications', headers=auth_headers('charlie'), json={
            'name': 'ForbiddenApp', 'owner_id': 1, 'access_levels': ['Read'],
        })
        assert resp.status_code == 403

    def test_it_admin_can_create_app(self, client, auth_headers):
        headers = auth_headers('grace')
        users = client.get('/api/users', headers=headers).get_json()['users']
        owner_id = next(u['id'] for u in users if u['role'] == 'app_owner')
        resp = client.post('/api/applications', headers=headers, json={
            'name': 'NewTestApp', 'owner_id': owner_id,
            'access_levels': ['Read', 'Write'],
        })
        assert resp.status_code == 201

    def test_employee_cannot_delete_app(self, client, auth_headers):
        h_emp = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_emp).get_json()['applications']
        resp = client.delete(f'/api/applications/{apps[0]["id"]}', headers=h_emp)
        assert resp.status_code == 403

    def test_it_admin_can_delete_app(self, client, auth_headers):
        headers = auth_headers('grace')
        apps = client.get('/api/applications', headers=headers).get_json()['applications']
        resp = client.delete(f'/api/applications/{apps[0]["id"]}', headers=headers)
        assert resp.status_code == 200

    def test_create_app_duplicate_name(self, client, auth_headers):
        headers = auth_headers('grace')
        users = client.get('/api/users', headers=headers).get_json()['users']
        owner_id = next(u['id'] for u in users if u['role'] == 'app_owner')
        resp = client.post('/api/applications', headers=headers, json={
            'name': 'JIRA', 'owner_id': owner_id, 'access_levels': ['Read'],
        })
        assert resp.status_code == 409


class TestUnauthenticatedAccess:
    """All protected endpoints reject unauthenticated requests."""

    def test_users_requires_auth(self, client):
        assert client.get('/api/users').status_code == 401

    def test_me_requires_auth(self, client):
        assert client.get('/api/auth/me').status_code == 401

    def test_applications_requires_auth(self, client):
        assert client.get('/api/applications').status_code == 401

    def test_create_user_requires_auth(self, client):
        resp = client.post('/api/users', json={
            'username': 'x', 'email': 'x@x.com',
            'password': 'x', 'full_name': 'X', 'role': 'employee',
        })
        assert resp.status_code == 401

    def test_create_app_requires_auth(self, client):
        resp = client.post('/api/applications', json={
            'name': 'X', 'owner_id': 1, 'access_levels': ['Read'],
        })
        assert resp.status_code == 401
