"""Tests for the audit log endpoint."""


class TestAuditLog:
    def test_auditor_can_view_logs(self, client, auth_headers):
        resp = client.get('/api/audit', headers=auth_headers('ivan'))
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'logs' in data
        assert 'total' in data
        assert len(data['logs']) >= 1

    def test_it_admin_can_view_logs(self, client, auth_headers):
        resp = client.get('/api/audit', headers=auth_headers('grace'))
        assert resp.status_code == 200

    def test_employee_cannot_view_logs(self, client, auth_headers):
        resp = client.get('/api/audit', headers=auth_headers('alice'))
        assert resp.status_code == 403

    def test_manager_cannot_view_logs(self, client, auth_headers):
        resp = client.get('/api/audit', headers=auth_headers('charlie'))
        assert resp.status_code == 403

    def test_filter_by_action(self, client, auth_headers):
        h = auth_headers('ivan')
        resp = client.get('/api/audit', headers=h,
                          query_string={'action': 'ACCESS_GRANTED'})
        assert resp.status_code == 200
        logs = resp.get_json()['logs']
        for log in logs:
            assert 'ACCESS_GRANTED' in log['action']

    def test_filter_by_entity_type(self, client, auth_headers):
        h = auth_headers('ivan')
        resp = client.get('/api/audit', headers=h,
                          query_string={'entity_type': 'AccessGrant'})
        assert resp.status_code == 200
        for log in resp.get_json()['logs']:
            assert log['entity_type'] == 'AccessGrant'

    def test_logs_include_username(self, client, auth_headers):
        resp = client.get('/api/audit', headers=auth_headers('ivan'))
        logs = resp.get_json()['logs']
        for log in logs:
            assert 'username' in log
            assert 'user_full_name' in log

    def test_pagination(self, client, auth_headers):
        h = auth_headers('ivan')
        resp = client.get('/api/audit', headers=h,
                          query_string={'page': 1, 'per_page': 2})
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['logs']) <= 2
        assert data['page'] == 1

    def test_audit_log_created_on_request(self, client, auth_headers):
        """Submitting a request must create an audit log entry."""
        h = auth_headers('alice')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': 'Audit log test',
        })
        h_auditor = auth_headers('ivan')
        resp = client.get('/api/audit', headers=h_auditor,
                          query_string={'action': 'REQUEST_CREATED'})
        logs = resp.get_json()['logs']
        assert len(logs) >= 1

    def test_audit_log_created_on_grant(self, client, auth_headers):
        """Granting access must create an audit log entry."""
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']
        jira = next((a for a in apps if a['name'] == 'JIRA'), apps[0])

        resp = client.post('/api/requests', headers=h_alice, json={
            'application_id': jira['id'], 'access_level': 'Read',
            'justification': 'Grant audit log test',
        })
        req_id = resp.get_json()['request']['id']
        client.post(f'/api/requests/{req_id}/approve', headers=auth_headers('charlie'), json={})
        client.post(f'/api/requests/{req_id}/approve', headers=auth_headers('eve'), json={})
        client.post('/api/fulfilment', headers=auth_headers('grace'),
                    json={'request_id': req_id})

        h_auditor = auth_headers('ivan')
        resp = client.get('/api/audit', headers=h_auditor,
                          query_string={'action': 'ACCESS_GRANTED'})
        logs = resp.get_json()['logs']
        assert len(logs) >= 1
        assert logs[0]['entity_type'] == 'AccessGrant'
