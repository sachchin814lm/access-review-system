"""Tests for fulfilment (grant/revoke) workflow."""


class TestGrantAccess:
    def _get_approved_request(self, client, h_admin):
        """Find the first approved request (from seed data)."""
        resp = client.get('/api/fulfilment/approved', headers=h_admin)
        assert resp.status_code == 200
        reqs = resp.get_json()['requests']
        return reqs[0] if reqs else None

    def _create_approved_request(self, client, auth_headers):
        """Submit + manager approve + owner approve a fresh request."""
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']
        jira = next((a for a in apps if a['name'] == 'JIRA'), apps[0])

        resp = client.post('/api/requests', headers=h_alice, json={
            'application_id': jira['id'],
            'access_level': 'Read',
            'justification': 'Fulfilment test',
        })
        req_id = resp.get_json()['request']['id']

        h_charlie = auth_headers('charlie')
        client.post(f'/api/requests/{req_id}/approve', headers=h_charlie, json={})

        h_eve = auth_headers('eve')
        client.post(f'/api/requests/{req_id}/approve', headers=h_eve, json={})

        return req_id

    def test_it_admin_grants_approved_request(self, client, auth_headers):
        h_grace = auth_headers('grace')
        req_id = self._create_approved_request(client, auth_headers)
        resp = client.post('/api/fulfilment', headers=h_grace,
                           json={'request_id': req_id})
        assert resp.status_code == 201
        grant = resp.get_json()['grant']
        assert grant['is_active'] is True
        assert grant['user_name'] is not None

    def test_grant_moves_request_to_granted(self, client, auth_headers):
        h_grace = auth_headers('grace')
        req_id = self._create_approved_request(client, auth_headers)
        client.post('/api/fulfilment', headers=h_grace, json={'request_id': req_id})

        h_alice = auth_headers('alice')
        req_data = client.get(f'/api/requests/{req_id}', headers=h_alice).get_json()['request']
        assert req_data['status'] == 'Granted'

    def test_employee_cannot_grant(self, client, auth_headers):
        req_id = self._create_approved_request(client, auth_headers)
        resp = client.post('/api/fulfilment', headers=auth_headers('alice'),
                           json={'request_id': req_id})
        assert resp.status_code == 403

    def test_manager_cannot_grant(self, client, auth_headers):
        req_id = self._create_approved_request(client, auth_headers)
        resp = client.post('/api/fulfilment', headers=auth_headers('charlie'),
                           json={'request_id': req_id})
        assert resp.status_code == 403

    def test_cannot_grant_non_approved_request(self, client, auth_headers):
        h_grace = auth_headers('grace')
        # req1 is 'Pending Manager Approval'
        reqs = client.get('/api/requests', headers=h_grace,
                          query_string={'status': 'Pending Manager Approval'}).get_json()['requests']
        req_id = reqs[0]['id']
        resp = client.post('/api/fulfilment', headers=h_grace, json={'request_id': req_id})
        assert resp.status_code == 400

    def test_cannot_grant_twice(self, client, auth_headers):
        h_grace = auth_headers('grace')
        req_id = self._create_approved_request(client, auth_headers)
        client.post('/api/fulfilment', headers=h_grace, json={'request_id': req_id})
        resp2 = client.post('/api/fulfilment', headers=h_grace, json={'request_id': req_id})
        assert resp2.status_code == 409

    def test_missing_request_id(self, client, auth_headers):
        resp = client.post('/api/fulfilment', headers=auth_headers('grace'), json={})
        assert resp.status_code == 400


class TestRevokeAccess:
    def _create_grant(self, client, auth_headers):
        """Create a fully-approved-then-granted access, returning grant_id."""
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']
        jira = next((a for a in apps if a['name'] == 'JIRA'), apps[0])

        resp = client.post('/api/requests', headers=h_alice, json={
            'application_id': jira['id'],
            'access_level': 'Read',
            'justification': 'Revoke test',
        })
        req_id = resp.get_json()['request']['id']

        h_charlie = auth_headers('charlie')
        client.post(f'/api/requests/{req_id}/approve', headers=h_charlie, json={})
        h_eve = auth_headers('eve')
        client.post(f'/api/requests/{req_id}/approve', headers=h_eve, json={})

        h_grace = auth_headers('grace')
        grant_resp = client.post('/api/fulfilment', headers=h_grace,
                                 json={'request_id': req_id})
        return grant_resp.get_json()['grant']['id']

    def test_it_admin_revokes_grant(self, client, auth_headers):
        grant_id = self._create_grant(client, auth_headers)
        h_grace = auth_headers('grace')
        resp = client.patch(f'/api/fulfilment/{grant_id}/revoke', headers=h_grace,
                            json={'revoke_reason': 'Role change'})
        assert resp.status_code == 200
        grant = resp.get_json()['grant']
        assert grant['is_active'] is False
        assert grant['revoke_reason'] == 'Role change'

    def test_revoke_requires_reason(self, client, auth_headers):
        grant_id = self._create_grant(client, auth_headers)
        h_grace = auth_headers('grace')
        resp = client.patch(f'/api/fulfilment/{grant_id}/revoke', headers=h_grace,
                            json={'revoke_reason': ''})
        assert resp.status_code == 400

    def test_cannot_revoke_already_revoked(self, client, auth_headers):
        grant_id = self._create_grant(client, auth_headers)
        h_grace = auth_headers('grace')
        client.patch(f'/api/fulfilment/{grant_id}/revoke', headers=h_grace,
                     json={'revoke_reason': 'First revoke'})
        resp = client.patch(f'/api/fulfilment/{grant_id}/revoke', headers=h_grace,
                            json={'revoke_reason': 'Second revoke'})
        assert resp.status_code == 400

    def test_employee_cannot_revoke(self, client, auth_headers):
        grant_id = self._create_grant(client, auth_headers)
        resp = client.patch(f'/api/fulfilment/{grant_id}/revoke',
                            headers=auth_headers('alice'),
                            json={'revoke_reason': 'Self revoke attempt'})
        assert resp.status_code == 403

    def test_revoke_updates_request_status(self, client, auth_headers):
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']
        jira = next((a for a in apps if a['name'] == 'JIRA'), apps[0])

        resp = client.post('/api/requests', headers=h_alice, json={
            'application_id': jira['id'], 'access_level': 'Read',
            'justification': 'Status track test',
        })
        req_id = resp.get_json()['request']['id']
        client.post(f'/api/requests/{req_id}/approve', headers=auth_headers('charlie'), json={})
        client.post(f'/api/requests/{req_id}/approve', headers=auth_headers('eve'), json={})
        grant_resp = client.post('/api/fulfilment', headers=auth_headers('grace'),
                                 json={'request_id': req_id})
        grant_id = grant_resp.get_json()['grant']['id']
        client.patch(f'/api/fulfilment/{grant_id}/revoke', headers=auth_headers('grace'),
                     json={'revoke_reason': 'Test'})

        req = client.get(f'/api/requests/{req_id}', headers=h_alice).get_json()['request']
        assert req['status'] == 'Revoked'
