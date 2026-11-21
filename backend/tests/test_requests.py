"""Tests for the access request and approval workflow."""


class TestSubmitRequest:
    def test_employee_can_submit_request(self, client, auth_headers):
        h = auth_headers('alice')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        app_id = apps[0]['id']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': app_id,
            'access_level': apps[0]['access_levels'][0],
            'justification': 'I need this for my project work',
        })
        assert resp.status_code == 201
        data = resp.get_json()['request']
        assert data['status'] == 'Pending Manager Approval'
        assert data['requester_id'] is not None

    def test_it_admin_cannot_submit_request(self, client, auth_headers):
        h = auth_headers('grace')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': 'Admin test',
        })
        assert resp.status_code == 403

    def test_auditor_cannot_submit_request(self, client, auth_headers):
        h = auth_headers('ivan')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': 'Auditor test',
        })
        assert resp.status_code == 403

    def test_missing_justification_rejected(self, client, auth_headers):
        h = auth_headers('alice')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': '',
        })
        assert resp.status_code == 400

    def test_invalid_access_level_rejected(self, client, auth_headers):
        h = auth_headers('alice')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': 'SuperAdmin',
            'justification': 'Need superadmin',
        })
        assert resp.status_code == 400

    def test_invalid_app_id_rejected(self, client, auth_headers):
        h = auth_headers('alice')
        resp = client.post('/api/requests', headers=h, json={
            'application_id': 99999,
            'access_level': 'Read',
            'justification': 'Test',
        })
        assert resp.status_code == 404

    def test_expiry_date_accepted(self, client, auth_headers):
        h = auth_headers('alice')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': 'Temporary access needed',
            'expiry_date': '2027-06-30',
        })
        assert resp.status_code == 201
        assert resp.get_json()['request']['expiry_date'] == '2027-06-30'

    def test_invalid_expiry_date_rejected(self, client, auth_headers):
        h = auth_headers('alice')
        apps = client.get('/api/applications', headers=h).get_json()['applications']
        resp = client.post('/api/requests', headers=h, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': 'Test',
            'expiry_date': 'not-a-date',
        })
        assert resp.status_code == 400


class TestMyRequests:
    def test_employee_sees_own_requests(self, client, auth_headers):
        h = auth_headers('alice')
        resp = client.get('/api/requests/mine', headers=h)
        assert resp.status_code == 200
        reqs = resp.get_json()['requests']
        assert len(reqs) > 0
        for r in reqs:
            assert 'application_name' in r

    def test_bob_sees_only_his_requests(self, client, auth_headers):
        h_bob = auth_headers('bob')
        h_alice = auth_headers('alice')
        alice_resp = client.get('/api/requests/mine', headers=h_alice).get_json()
        bob_resp = client.get('/api/requests/mine', headers=h_bob).get_json()
        alice_ids = {r['id'] for r in alice_resp['requests']}
        bob_ids = {r['id'] for r in bob_resp['requests']}
        assert alice_ids.isdisjoint(bob_ids), "Alice and Bob should not share request IDs"


class TestManagerApproval:
    def _get_pending_manager_request(self, client, h_manager):
        """Get first pending request visible to this manager."""
        resp = client.get('/api/requests/pending', headers=h_manager)
        assert resp.status_code == 200
        reqs = resp.get_json()['requests']
        return reqs[0] if reqs else None

    def test_manager_sees_pending_requests(self, client, auth_headers):
        h = auth_headers('charlie')
        resp = client.get('/api/requests/pending', headers=h)
        assert resp.status_code == 200
        # charlie manages alice who has req1 pending manager approval
        reqs = resp.get_json()['requests']
        assert len(reqs) >= 1
        assert all(r['status'] == 'Pending Manager Approval' for r in reqs)

    def test_employee_cannot_see_pending(self, client, auth_headers):
        resp = client.get('/api/requests/pending', headers=auth_headers('alice'))
        assert resp.status_code == 403

    def test_manager_approves_direct_report_request(self, client, auth_headers):
        h_manager = auth_headers('charlie')
        req = self._get_pending_manager_request(client, h_manager)
        assert req is not None, "charlie should have pending requests"
        resp = client.post(f'/api/requests/{req["id"]}/approve', headers=h_manager,
                           json={'comments': 'Looks reasonable'})
        assert resp.status_code == 200
        updated = resp.get_json()['request']
        assert updated['status'] == 'Pending Owner Approval'

    def test_manager_rejects_request(self, client, auth_headers):
        h = auth_headers('charlie')
        req = self._get_pending_manager_request(client, h)
        assert req is not None
        resp = client.post(f'/api/requests/{req["id"]}/reject', headers=h,
                           json={'comments': 'Not justified'})
        assert resp.status_code == 200
        assert resp.get_json()['request']['status'] == 'Rejected'

    def test_manager_cannot_approve_non_report(self, client, auth_headers):
        # diana manages bob; charlie tries to approve bob's requests
        h_diana = auth_headers('diana')
        h_charlie = auth_headers('charlie')
        diana_reqs = client.get('/api/requests/pending', headers=h_diana).get_json()['requests']
        if not diana_reqs:
            return  # skip if no requests pending for diana
        bob_req = diana_reqs[0]
        resp = client.post(f'/api/requests/{bob_req["id"]}/approve',
                           headers=h_charlie, json={'comments': 'Cross-approve attempt'})
        assert resp.status_code == 403

    def test_employee_cannot_approve(self, client, auth_headers):
        h_manager = auth_headers('charlie')
        req = self._get_pending_manager_request(client, h_manager)
        if not req:
            return
        resp = client.post(f'/api/requests/{req["id"]}/approve',
                           headers=auth_headers('alice'), json={})
        assert resp.status_code == 403

    def test_auditor_cannot_approve(self, client, auth_headers):
        h_manager = auth_headers('charlie')
        req = self._get_pending_manager_request(client, h_manager)
        if not req:
            return
        resp = client.post(f'/api/requests/{req["id"]}/approve',
                           headers=auth_headers('ivan'), json={})
        assert resp.status_code == 403


class TestOwnerApproval:
    def _advance_to_owner_stage(self, client, auth_headers):
        """Submit + manager-approve a request so it reaches owner stage."""
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']
        # Find the JIRA app owned by eve
        jira = next((a for a in apps if a['name'] == 'JIRA'), apps[0])

        client.post('/api/requests', headers=h_alice, json={
            'application_id': jira['id'],
            'access_level': jira['access_levels'][0],
            'justification': 'Owner approval test',
        })
        h_charlie = auth_headers('charlie')
        pending = client.get('/api/requests/pending', headers=h_charlie).get_json()['requests']
        new_req = pending[-1]
        client.post(f'/api/requests/{new_req["id"]}/approve', headers=h_charlie,
                    json={'comments': 'Manager approved'})
        return new_req['id']

    def test_owner_approves_request(self, client, auth_headers):
        req_id = self._advance_to_owner_stage(client, auth_headers)
        h_eve = auth_headers('eve')
        pending = client.get('/api/requests/pending', headers=h_eve).get_json()['requests']
        req = next((r for r in pending if r['id'] == req_id), None)
        assert req is not None, "eve should see this request pending owner approval"
        resp = client.post(f'/api/requests/{req_id}/approve', headers=h_eve,
                           json={'comments': 'Approved by owner'})
        assert resp.status_code == 200
        assert resp.get_json()['request']['status'] == 'Approved'

    def test_owner_cannot_approve_wrong_app(self, client, auth_headers):
        req_id = self._advance_to_owner_stage(client, auth_headers)
        # frank owns GitHub/AWS, not JIRA — should be denied
        resp = client.post(f'/api/requests/{req_id}/approve', headers=auth_headers('frank'),
                           json={'comments': 'Wrong owner'})
        assert resp.status_code in (403, 400)

    def test_owner_rejects_request(self, client, auth_headers):
        req_id = self._advance_to_owner_stage(client, auth_headers)
        h_eve = auth_headers('eve')
        resp = client.post(f'/api/requests/{req_id}/reject', headers=h_eve,
                           json={'comments': 'Access not approved'})
        assert resp.status_code == 200
        assert resp.get_json()['request']['status'] == 'Rejected'


class TestFullApprovalChain:
    def test_full_happy_path(self, client, auth_headers):
        """Submit → manager approve → owner approve → Approved."""
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']
        jira = next((a for a in apps if a['name'] == 'JIRA'), apps[0])

        # Submit
        resp = client.post('/api/requests', headers=h_alice, json={
            'application_id': jira['id'],
            'access_level': 'Read',
            'justification': 'Need for project review',
        })
        assert resp.status_code == 201
        req_id = resp.get_json()['request']['id']

        # Manager approves
        h_charlie = auth_headers('charlie')
        resp = client.post(f'/api/requests/{req_id}/approve', headers=h_charlie,
                           json={'comments': 'Approved by manager'})
        assert resp.status_code == 200
        assert resp.get_json()['request']['status'] == 'Pending Owner Approval'

        # Owner approves
        h_eve = auth_headers('eve')
        resp = client.post(f'/api/requests/{req_id}/approve', headers=h_eve,
                           json={'comments': 'Approved by owner'})
        assert resp.status_code == 200
        assert resp.get_json()['request']['status'] == 'Approved'

        # Approvals are recorded
        resp = client.get(f'/api/requests/{req_id}', headers=h_alice)
        req_data = resp.get_json()['request']
        assert len(req_data['approvals']) == 2
        decisions = {a['approval_type']: a['decision'] for a in req_data['approvals']}
        assert decisions['manager'] == 'approved'
        assert decisions['app_owner'] == 'approved'

    def test_rejection_at_manager_stage(self, client, auth_headers):
        """Submit → manager reject → Rejected (owner never involved)."""
        h_alice = auth_headers('alice')
        apps = client.get('/api/applications', headers=h_alice).get_json()['applications']

        resp = client.post('/api/requests', headers=h_alice, json={
            'application_id': apps[0]['id'],
            'access_level': apps[0]['access_levels'][0],
            'justification': 'Should be rejected',
        })
        req_id = resp.get_json()['request']['id']

        h_charlie = auth_headers('charlie')
        resp = client.post(f'/api/requests/{req_id}/reject', headers=h_charlie,
                           json={'comments': 'Not justified'})
        assert resp.status_code == 200
        assert resp.get_json()['request']['status'] == 'Rejected'

        # Can't approve a rejected request
        h_eve = auth_headers('eve')
        resp = client.post(f'/api/requests/{req_id}/approve', headers=h_eve, json={})
        assert resp.status_code == 400
