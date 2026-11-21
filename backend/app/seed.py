"""Seed the database with demo data for all five roles."""

import json
from datetime import datetime, timedelta, date

from app import db
from app.models import (
    User, Application, AccessRequest, Approval,
    AccessGrant, ReviewCampaign, ReviewItem, AuditLog, Session,
)
from app.auth import hash_password


def seed():
    """Populate the database with demo users, apps, requests, grants, and a campaign."""

    # Clear existing data in dependency order
    for model in [AuditLog, ReviewItem, ReviewCampaign, AccessGrant,
                  Approval, AccessRequest, Application, Session, User]:
        db.session.query(model).delete()
    db.session.commit()

    pw = hash_password('password123')
    now = datetime.utcnow()

    # ── Users ────────────────────────────────────────────────────────────
    grace   = User(username='grace',   email='grace@example.com',   password_hash=pw, full_name='Grace Hopper',   role='it_admin')
    heidi   = User(username='heidi',   email='heidi@example.com',   password_hash=pw, full_name='Heidi Lamarr',   role='it_admin')
    charlie = User(username='charlie', email='charlie@example.com', password_hash=pw, full_name='Charlie Chen',   role='manager')
    diana   = User(username='diana',   email='diana@example.com',   password_hash=pw, full_name='Diana Prince',   role='manager')
    eve     = User(username='eve',     email='eve@example.com',     password_hash=pw, full_name='Eve Torres',     role='app_owner')
    frank   = User(username='frank',   email='frank@example.com',   password_hash=pw, full_name='Frank Castle',   role='app_owner')
    ivan    = User(username='ivan',    email='ivan@example.com',    password_hash=pw, full_name='Ivan Petrov',    role='auditor')
    judy    = User(username='judy',    email='judy@example.com',    password_hash=pw, full_name='Judy Hopps',     role='auditor')
    alice   = User(username='alice',   email='alice@example.com',   password_hash=pw, full_name='Alice Johnson',  role='employee')
    bob     = User(username='bob',     email='bob@example.com',     password_hash=pw, full_name='Bob Smith',      role='employee')

    db.session.add_all([grace, heidi, charlie, diana, eve, frank, ivan, judy, alice, bob])
    db.session.flush()

    # Manager relationships
    alice.manager_id = charlie.id
    bob.manager_id   = diana.id
    eve.manager_id   = charlie.id
    frank.manager_id = diana.id
    db.session.flush()

    # ── Applications ─────────────────────────────────────────────────────
    apps_data = [
        ('JIRA',        'Project tracking and issue management',      eve.id,   ['Read', 'Write', 'Admin']),
        ('Confluence',  'Team wiki and documentation',                eve.id,   ['Read', 'Write', 'Admin']),
        ('GitHub',      'Source code repository',                     frank.id, ['Read', 'Write', 'Admin']),
        ('AWS Console', 'Cloud infrastructure management',            frank.id, ['Read', 'PowerUser', 'Admin']),
        ('Salesforce',  'Customer relationship management',           eve.id,   ['Read', 'Write', 'Admin']),
    ]
    app_objs = {}
    for name, desc, owner_id, levels in apps_data:
        a = Application(name=name, description=desc, owner_id=owner_id)
        a.access_levels = levels
        db.session.add(a)
        app_objs[name] = a
    db.session.flush()

    jira       = app_objs['JIRA']
    confluence = app_objs['Confluence']
    github     = app_objs['GitHub']
    aws        = app_objs['AWS Console']
    salesforce = app_objs['Salesforce']

    # ── Access Requests (various states) ─────────────────────────────────
    req1 = AccessRequest(
        requester_id=alice.id, application_id=jira.id,
        access_level='Write', justification='Need write access for sprint planning',
        status='Pending Manager Approval', created_at=now - timedelta(days=1),
    )
    req2 = AccessRequest(
        requester_id=alice.id, application_id=github.id,
        access_level='Read', justification='Need to review code for QA',
        status='Granted', created_at=now - timedelta(days=10),
    )
    req3 = AccessRequest(
        requester_id=bob.id, application_id=confluence.id,
        access_level='Write', justification='Need to update team documentation',
        status='Pending Owner Approval', created_at=now - timedelta(days=3),
    )
    req4 = AccessRequest(
        requester_id=bob.id, application_id=aws.id,
        access_level='Admin', justification='Need admin access for deployment',
        status='Rejected', created_at=now - timedelta(days=5),
    )
    req5 = AccessRequest(
        requester_id=alice.id, application_id=salesforce.id,
        access_level='Read', justification='Need to view customer data for reports',
        status='Granted', created_at=now - timedelta(days=15),
    )
    req6 = AccessRequest(
        requester_id=bob.id, application_id=jira.id,
        access_level='Read', justification='Need read access for project tracking',
        status='Revoked', created_at=now - timedelta(days=20),
    )
    req7 = AccessRequest(
        requester_id=alice.id, application_id=aws.id,
        access_level='Read', justification='Need read access for monitoring',
        status='Approved', created_at=now - timedelta(days=2),
    )
    req8 = AccessRequest(
        requester_id=bob.id, application_id=github.id,
        access_level='Write', justification='Need to push code changes',
        status='Pending Manager Approval', created_at=now - timedelta(hours=6),
    )

    db.session.add_all([req1, req2, req3, req4, req5, req6, req7, req8])
    db.session.flush()

    # ── Approvals ────────────────────────────────────────────────────────
    approvals = [
        # req2 fully approved
        Approval(request_id=req2.id, approver_id=charlie.id, approval_type='manager',
                 decision='approved', comments='Looks good',
                 decided_at=now - timedelta(days=9)),
        Approval(request_id=req2.id, approver_id=frank.id, approval_type='app_owner',
                 decision='approved', comments='Approved for QA',
                 decided_at=now - timedelta(days=8)),
        # req3 manager approved, pending owner
        Approval(request_id=req3.id, approver_id=diana.id, approval_type='manager',
                 decision='approved', comments='Approved',
                 decided_at=now - timedelta(days=2)),
        # req4 manager rejected
        Approval(request_id=req4.id, approver_id=diana.id, approval_type='manager',
                 decision='rejected', comments='Admin access not justified for this role',
                 decided_at=now - timedelta(days=4)),
        # req5 fully approved
        Approval(request_id=req5.id, approver_id=charlie.id, approval_type='manager',
                 decision='approved', comments='OK',
                 decided_at=now - timedelta(days=14)),
        Approval(request_id=req5.id, approver_id=eve.id, approval_type='app_owner',
                 decision='approved', comments='Read access approved',
                 decided_at=now - timedelta(days=13)),
        # req6 fully approved (then granted then revoked)
        Approval(request_id=req6.id, approver_id=diana.id, approval_type='manager',
                 decision='approved', comments='OK',
                 decided_at=now - timedelta(days=19)),
        Approval(request_id=req6.id, approver_id=eve.id, approval_type='app_owner',
                 decision='approved', comments='Approved',
                 decided_at=now - timedelta(days=18)),
        # req7 fully approved, awaiting fulfilment
        Approval(request_id=req7.id, approver_id=charlie.id, approval_type='manager',
                 decision='approved', comments='Monitoring access is fine',
                 decided_at=now - timedelta(days=1)),
        Approval(request_id=req7.id, approver_id=frank.id, approval_type='app_owner',
                 decision='approved', comments='Read-only approved',
                 decided_at=now - timedelta(hours=12)),
    ]
    db.session.add_all(approvals)
    db.session.flush()

    # ── Access Grants ────────────────────────────────────────────────────
    grant1 = AccessGrant(
        request_id=req2.id, user_id=alice.id, application_id=github.id,
        access_level='Read', granted_at=now - timedelta(days=7),
        granted_by_id=grace.id, is_active=True,
    )
    grant2 = AccessGrant(
        request_id=req5.id, user_id=alice.id, application_id=salesforce.id,
        access_level='Read', granted_at=now - timedelta(days=12),
        granted_by_id=grace.id, is_active=True,
    )
    grant3 = AccessGrant(
        request_id=req6.id, user_id=bob.id, application_id=jira.id,
        access_level='Read', granted_at=now - timedelta(days=17),
        granted_by_id=grace.id, is_active=False,
        revoked_at=now - timedelta(days=5),
        revoke_reason='Project ended, access no longer needed',
        revoked_by_id=grace.id,
    )
    grant4 = AccessGrant(
        request_id=None, user_id=bob.id, application_id=confluence.id,
        access_level='Read', granted_at=now - timedelta(days=30),
        granted_by_id=grace.id, is_active=True,
    )

    db.session.add_all([grant1, grant2, grant3, grant4])
    db.session.flush()

    # ── Review Campaign ──────────────────────────────────────────────────
    campaign = ReviewCampaign(
        name='Q4 2026 Access Review',
        description='Quarterly review of all active access grants',
        scope='all', due_date=date(2026, 12, 15),
        status='Active', created_by_id=grace.id,
        created_at=now - timedelta(days=2),
    )
    db.session.add(campaign)
    db.session.flush()

    ri1 = ReviewItem(campaign_id=campaign.id, grant_id=grant1.id, reviewer_id=charlie.id)
    ri2 = ReviewItem(campaign_id=campaign.id, grant_id=grant2.id, reviewer_id=charlie.id)
    ri3 = ReviewItem(campaign_id=campaign.id, grant_id=grant4.id, reviewer_id=diana.id)

    db.session.add_all([ri1, ri2, ri3])
    db.session.flush()

    # ── Audit Log ────────────────────────────────────────────────────────
    audit_entries = [
        AuditLog(user_id=alice.id, action='REQUEST_CREATED', entity_type='AccessRequest',
                 entity_id=req1.id, after_state=json.dumps(req1.to_dict()),
                 timestamp=req1.created_at),
        AuditLog(user_id=alice.id, action='REQUEST_CREATED', entity_type='AccessRequest',
                 entity_id=req2.id, after_state=json.dumps(req2.to_dict()),
                 timestamp=req2.created_at),
        AuditLog(user_id=charlie.id, action='MANAGER_APPROVED', entity_type='AccessRequest',
                 entity_id=req2.id, after_state=json.dumps({'status': 'Pending Owner Approval'}),
                 timestamp=now - timedelta(days=9)),
        AuditLog(user_id=frank.id, action='OWNER_APPROVED', entity_type='AccessRequest',
                 entity_id=req2.id, after_state=json.dumps({'status': 'Approved'}),
                 timestamp=now - timedelta(days=8)),
        AuditLog(user_id=grace.id, action='ACCESS_GRANTED', entity_type='AccessGrant',
                 entity_id=grant1.id, after_state=json.dumps(grant1.to_dict()),
                 timestamp=grant1.granted_at),
        AuditLog(user_id=grace.id, action='ACCESS_REVOKED', entity_type='AccessGrant',
                 entity_id=grant3.id, after_state=json.dumps(grant3.to_dict()),
                 timestamp=grant3.revoked_at),
        AuditLog(user_id=grace.id, action='CAMPAIGN_CREATED', entity_type='ReviewCampaign',
                 entity_id=campaign.id, after_state=json.dumps(campaign.to_dict()),
                 timestamp=campaign.created_at),
    ]
    db.session.add_all(audit_entries)
    db.session.commit()

    print('Database seeded successfully!')
    print(f'  Users:            {User.query.count()}')
    print(f'  Applications:     {Application.query.count()}')
    print(f'  Access Requests:  {AccessRequest.query.count()}')
    print(f'  Approvals:        {Approval.query.count()}')
    print(f'  Access Grants:    {AccessGrant.query.count()}')
    print(f'  Review Campaigns: {ReviewCampaign.query.count()}')
    print(f'  Review Items:     {ReviewItem.query.count()}')
    print(f'  Audit Log:        {AuditLog.query.count()}')


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed()
