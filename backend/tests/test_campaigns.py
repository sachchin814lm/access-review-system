"""Tests for review campaigns."""
from datetime import date, timedelta


class TestCreateCampaign:
    def test_it_admin_creates_campaign(self, client, auth_headers):
        h = auth_headers('grace')
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=h, json={
            'name': 'Test Campaign',
            'description': 'A test review campaign',
            'scope': 'all',
            'due_date': future,
        })
        assert resp.status_code == 201
        c = resp.get_json()['campaign']
        assert c['name'] == 'Test Campaign'
        assert c['status'] == 'Active'
        assert c['items_created'] >= 0

    def test_employee_cannot_create_campaign(self, client, auth_headers):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=auth_headers('alice'), json={
            'name': 'Forbidden', 'scope': 'all', 'due_date': future,
        })
        assert resp.status_code == 403

    def test_manager_cannot_create_campaign(self, client, auth_headers):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=auth_headers('charlie'), json={
            'name': 'Forbidden', 'scope': 'all', 'due_date': future,
        })
        assert resp.status_code == 403

    def test_past_due_date_rejected(self, client, auth_headers):
        past = (date.today() - timedelta(days=1)).isoformat()
        resp = client.post('/api/campaigns', headers=auth_headers('grace'), json={
            'name': 'Past', 'scope': 'all', 'due_date': past,
        })
        assert resp.status_code == 400

    def test_missing_name_rejected(self, client, auth_headers):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=auth_headers('grace'), json={
            'scope': 'all', 'due_date': future,
        })
        assert resp.status_code == 400

    def test_campaign_generates_review_items(self, client, auth_headers):
        h = auth_headers('grace')
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=h, json={
            'name': 'Item Generation Test', 'scope': 'all', 'due_date': future,
        })
        assert resp.status_code == 201
        # Seed has 3 active grants (grant1, grant2, grant4)
        assert resp.get_json()['campaign']['items_created'] >= 3

    def test_application_scope_campaign(self, client, auth_headers):
        h = auth_headers('grace')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        app_id = apps[0]['id']
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=h, json={
            'name': 'App Scope Campaign', 'scope': 'application',
            'scope_ref_id': app_id, 'due_date': future,
        })
        assert resp.status_code == 201


class TestListCampaigns:
    def test_admin_sees_all_campaigns(self, client, auth_headers):
        h = auth_headers('grace')
        resp = client.get('/api/campaigns', headers=h)
        assert resp.status_code == 200
        assert len(resp.get_json()['campaigns']) >= 1  # seed has 1

    def test_auditor_sees_all_campaigns(self, client, auth_headers):
        resp = client.get('/api/campaigns', headers=auth_headers('ivan'))
        assert resp.status_code == 200

    def test_employee_cannot_list_campaigns(self, client, auth_headers):
        resp = client.get('/api/campaigns', headers=auth_headers('alice'))
        assert resp.status_code == 403

    def test_manager_sees_own_campaigns(self, client, auth_headers):
        # charlie is a reviewer in the seed campaign
        resp = client.get('/api/campaigns', headers=auth_headers('charlie'))
        assert resp.status_code == 200


class TestReviewDecisions:
    def _create_campaign_with_items(self, client, auth_headers):
        """Create a campaign and return (campaign_id, first item from charlie's view)."""
        h_grace = auth_headers('grace')
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post('/api/campaigns', headers=h_grace, json={
            'name': 'Decision Test Campaign', 'scope': 'all', 'due_date': future,
        })
        campaign_id = resp.get_json()['campaign']['id']
        # Get items for charlie
        detail = client.get(f'/api/campaigns/{campaign_id}',
                            headers=auth_headers('charlie')).get_json()['campaign']
        items = detail.get('items', [])
        return campaign_id, items

    def test_reviewer_can_keep(self, client, auth_headers):
        campaign_id, items = self._create_campaign_with_items(client, auth_headers)
        if not items:
            return
        item_id = items[0]['id']
        resp = client.post(f'/api/campaigns/{campaign_id}/items/{item_id}/decide',
                           headers=auth_headers('charlie'),
                           json={'decision': 'Keep', 'comments': 'Still needed'})
        assert resp.status_code == 200
        assert resp.get_json()['item']['decision'] == 'Keep'

    def test_reviewer_can_revoke(self, client, auth_headers):
        campaign_id, items = self._create_campaign_with_items(client, auth_headers)
        if not items:
            return
        item_id = items[0]['id']
        resp = client.post(f'/api/campaigns/{campaign_id}/items/{item_id}/decide',
                           headers=auth_headers('charlie'),
                           json={'decision': 'Revoke', 'comments': 'No longer needed'})
        assert resp.status_code == 200
        assert resp.get_json()['item']['decision'] == 'Revoke'

    def test_invalid_decision_rejected(self, client, auth_headers):
        campaign_id, items = self._create_campaign_with_items(client, auth_headers)
        if not items:
            return
        item_id = items[0]['id']
        resp = client.post(f'/api/campaigns/{campaign_id}/items/{item_id}/decide',
                           headers=auth_headers('charlie'),
                           json={'decision': 'Maybe'})
        assert resp.status_code == 400

    def test_non_reviewer_cannot_decide(self, client, auth_headers):
        campaign_id, items = self._create_campaign_with_items(client, auth_headers)
        if not items:
            return
        item_id = items[0]['id']
        # frank is not charlie's reviewer
        resp = client.post(f'/api/campaigns/{campaign_id}/items/{item_id}/decide',
                           headers=auth_headers('frank'),
                           json={'decision': 'Keep'})
        assert resp.status_code == 403

    def test_cannot_decide_twice(self, client, auth_headers):
        campaign_id, items = self._create_campaign_with_items(client, auth_headers)
        if not items:
            return
        item_id = items[0]['id']
        h = auth_headers('charlie')
        client.post(f'/api/campaigns/{campaign_id}/items/{item_id}/decide',
                    headers=h, json={'decision': 'Keep'})
        resp = client.post(f'/api/campaigns/{campaign_id}/items/{item_id}/decide',
                           headers=h, json={'decision': 'Revoke'})
        assert resp.status_code == 400

    def test_campaign_completes_when_all_decided(self, client, auth_headers):
        campaign_id, _ = self._create_campaign_with_items(client, auth_headers)

        h_grace = auth_headers('grace')
        detail = client.get(f'/api/campaigns/{campaign_id}',
                            headers=h_grace).get_json()['campaign']
        all_items = detail.get('items', [])
        assert len(all_items) > 0

        # Admin decides all items
        for item in all_items:
            client.post(f'/api/campaigns/{campaign_id}/items/{item["id"]}/decide',
                        headers=h_grace,
                        json={'decision': 'Keep', 'comments': 'admin bulk decide'})

        campaign = client.get(f'/api/campaigns/{campaign_id}',
                              headers=h_grace).get_json()['campaign']
        assert campaign['completion_pct'] == 100.0
        assert campaign['status'] == 'Completed'

    def test_campaign_completion_percentage(self, client, auth_headers):
        campaign_id, items = self._create_campaign_with_items(client, auth_headers)
        if len(items) < 2:
            return

        h = auth_headers('charlie')
        client.post(f'/api/campaigns/{campaign_id}/items/{items[0]["id"]}/decide',
                    headers=h, json={'decision': 'Keep'})

        campaign = client.get(f'/api/campaigns/{campaign_id}',
                              headers=auth_headers('grace')).get_json()['campaign']
        total = campaign['total_items']
        decided = campaign['decided_items']
        expected_pct = round(decided / total * 100, 1) if total else 0.0
        assert campaign['completion_pct'] == expected_pct


class TestCancelCampaign:
    def test_admin_cancels_campaign(self, client, auth_headers):
        h = auth_headers('grace')
        # Use the seed campaign
        campaigns = client.get('/api/campaigns', headers=h).get_json()['campaigns']
        active = next((c for c in campaigns if c['status'] == 'Active'), None)
        assert active is not None
        resp = client.post(f'/api/campaigns/{active["id"]}/cancel', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['campaign']['status'] == 'Cancelled'

    def test_employee_cannot_cancel(self, client, auth_headers):
        h = auth_headers('grace')
        campaigns = client.get('/api/campaigns', headers=h).get_json()['campaigns']
        active = next((c for c in campaigns if c['status'] == 'Active'), None)
        if not active:
            return
        resp = client.post(f'/api/campaigns/{active["id"]}/cancel',
                           headers=auth_headers('alice'))
        assert resp.status_code == 403
