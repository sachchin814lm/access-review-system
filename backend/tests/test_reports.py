"""Tests for all report endpoints."""


class TestReports:
    def test_access_by_user_json(self, client, auth_headers):
        resp = client.get('/api/reports/access-by-user', headers=auth_headers('ivan'))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['report'] == 'access_by_user'
        assert isinstance(data['rows'], list)
        for row in data['rows']:
            assert 'user_name' in row
            assert 'application' in row

    def test_access_by_user_csv(self, client, auth_headers):
        resp = client.get('/api/reports/access-by-user',
                          headers=auth_headers('ivan'),
                          query_string={'format': 'csv'})
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type
        assert b'user_name' in resp.data

    def test_access_by_application_json(self, client, auth_headers):
        resp = client.get('/api/reports/access-by-application', headers=auth_headers('grace'))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['report'] == 'access_by_application'

    def test_access_by_application_csv(self, client, auth_headers):
        resp = client.get('/api/reports/access-by-application',
                          headers=auth_headers('grace'),
                          query_string={'format': 'csv'})
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type

    def test_pending_approvals_report(self, client, auth_headers):
        resp = client.get('/api/reports/pending-approvals', headers=auth_headers('ivan'))
        assert resp.status_code == 200
        data = resp.get_json()
        for row in data['rows']:
            assert row['status'] in ('Pending Manager Approval', 'Pending Owner Approval')

    def test_pending_approvals_csv(self, client, auth_headers):
        resp = client.get('/api/reports/pending-approvals',
                          headers=auth_headers('ivan'),
                          query_string={'format': 'csv'})
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type

    def test_revoked_access_report(self, client, auth_headers):
        resp = client.get('/api/reports/revoked-access', headers=auth_headers('ivan'))
        assert resp.status_code == 200
        data = resp.get_json()
        # Seed has grant3 as revoked
        assert len(data['rows']) >= 1
        for row in data['rows']:
            assert 'revoke_reason' in row
            assert 'revoked_at' in row

    def test_revoked_access_csv(self, client, auth_headers):
        resp = client.get('/api/reports/revoked-access',
                          headers=auth_headers('grace'),
                          query_string={'format': 'csv'})
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type

    def test_campaign_results_report(self, client, auth_headers):
        h = auth_headers('grace')
        campaigns = client.get('/api/campaigns', headers=h).get_json()['campaigns']
        campaign_id = campaigns[0]['id']
        resp = client.get('/api/reports/campaign-results',
                          headers=auth_headers('ivan'),
                          query_string={'campaign_id': campaign_id})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'summary' in data
        assert 'total' in data['summary']

    def test_campaign_results_csv(self, client, auth_headers):
        h = auth_headers('grace')
        campaigns = client.get('/api/campaigns', headers=h).get_json()['campaigns']
        campaign_id = campaigns[0]['id']
        resp = client.get('/api/reports/campaign-results',
                          headers=auth_headers('ivan'),
                          query_string={'campaign_id': campaign_id, 'format': 'csv'})
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type

    def test_campaign_results_missing_id(self, client, auth_headers):
        resp = client.get('/api/reports/campaign-results', headers=auth_headers('ivan'))
        assert resp.status_code == 400

    def test_overdue_reviews_report(self, client, auth_headers):
        resp = client.get('/api/reports/overdue-reviews', headers=auth_headers('ivan'))
        assert resp.status_code == 200
        # Seed campaign is not overdue yet, so rows should be empty
        assert isinstance(resp.get_json()['rows'], list)

    def test_employee_cannot_access_reports(self, client, auth_headers):
        endpoints = [
            '/api/reports/access-by-user',
            '/api/reports/access-by-application',
            '/api/reports/pending-approvals',
            '/api/reports/revoked-access',
            '/api/reports/overdue-reviews',
        ]
        h = auth_headers('alice')
        for ep in endpoints:
            resp = client.get(ep, headers=h)
            assert resp.status_code == 403, f'{ep} should return 403 for employees'

    def test_manager_cannot_access_reports(self, client, auth_headers):
        resp = client.get('/api/reports/access-by-user', headers=auth_headers('charlie'))
        assert resp.status_code == 403
