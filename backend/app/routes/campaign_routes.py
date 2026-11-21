import json
from datetime import datetime, date
from flask import Blueprint, request, jsonify

from app import db
from app.auth import get_current_user
from app.models import (
    ReviewCampaign, ReviewItem, AccessGrant, AuditLog, User, Application
)
from app.rbac import require_role, login_required

campaign_bp = Blueprint('campaigns', __name__)


def _log(user_id, action, entity_type, entity_id, before=None, after=None):
    db.session.add(AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=json.dumps(before) if before else None,
        after_state=json.dumps(after) if after else None,
        timestamp=datetime.utcnow(),
    ))


def _campaign_detail(campaign, user):
    """Build a rich campaign dict with items and progress."""
    d = campaign.to_dict()

    all_items = campaign.items.all()
    total = len(all_items)
    decided = sum(1 for i in all_items if i.decision != 'Pending')
    today = date.today()
    overdue = (
        sum(1 for i in all_items if i.decision == 'Pending')
        if campaign.due_date < today and campaign.status == 'Active'
        else 0
    )

    d['total_items'] = total
    d['decided_items'] = decided
    d['completion_pct'] = round(decided / total * 100, 1) if total else 0.0
    d['overdue_items'] = overdue

    if user.role in ('it_admin', 'auditor'):
        d['items'] = [_enrich_item(i) for i in all_items]
    else:
        my_items = [i for i in all_items if i.reviewer_id == user.id]
        d['items'] = [_enrich_item(i) for i in my_items]

    return d


def _enrich_item(item):
    d = item.to_dict()
    if item.grant:
        d['user_name'] = item.grant.user.full_name if item.grant.user else None
        d['application_name'] = item.grant.application.name if item.grant.application else None
        d['access_level'] = item.grant.access_level
    if item.reviewer:
        d['reviewer_name'] = item.reviewer.full_name
    return d


@campaign_bp.route('', methods=['POST'])
@require_role('it_admin')
def create_campaign():
    """Create a review campaign and auto-generate review items. IT Admin only."""
    user = get_current_user()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    name = (data.get('name') or '').strip()
    due_date_str = (data.get('due_date') or '').strip()
    scope = (data.get('scope') or 'all').strip()

    if not name:
        return jsonify({'error': 'name is required'}), 400
    if not due_date_str:
        return jsonify({'error': 'due_date is required'}), 400
    if scope not in ('all', 'application'):
        return jsonify({'error': 'scope must be "all" or "application"'}), 400

    try:
        due_date = date.fromisoformat(due_date_str)
    except ValueError:
        return jsonify({'error': 'due_date must be YYYY-MM-DD'}), 400

    if due_date <= date.today():
        return jsonify({'error': 'due_date must be in the future'}), 400

    scope_ref_id = data.get('scope_ref_id')
    if scope == 'application' and not scope_ref_id:
        return jsonify({'error': 'scope_ref_id (application_id) is required for application scope'}), 400

    campaign = ReviewCampaign(
        name=name,
        description=(data.get('description') or '').strip(),
        scope=scope,
        scope_ref_id=scope_ref_id,
        due_date=due_date,
        status='Active',
        created_by_id=user.id,
    )
    db.session.add(campaign)
    db.session.flush()

    # Generate review items for all matching active grants
    query = AccessGrant.query.filter_by(is_active=True)
    if scope == 'application':
        query = query.filter_by(application_id=scope_ref_id)
    grants = query.all()

    items_created = 0
    for grant in grants:
        # Determine reviewer: use the user's manager (if grant user has one),
        # else fall back to the application owner
        reviewer_id = None
        grant_user = db.session.get(User, grant.user_id)
        if grant_user and grant_user.manager_id:
            reviewer_id = grant_user.manager_id
        elif grant.application and grant.application.owner_id:
            reviewer_id = grant.application.owner_id

        if not reviewer_id:
            continue  # skip grants with no assignable reviewer

        item = ReviewItem(
            campaign_id=campaign.id,
            grant_id=grant.id,
            reviewer_id=reviewer_id,
        )
        db.session.add(item)
        items_created += 1

    _log(user.id, 'CAMPAIGN_CREATED', 'ReviewCampaign', campaign.id, after=campaign.to_dict())
    db.session.commit()

    d = campaign.to_dict()
    d['items_created'] = items_created
    return jsonify({'campaign': d}), 201


@campaign_bp.route('', methods=['GET'])
@require_role('it_admin', 'auditor', 'manager', 'app_owner')
def list_campaigns():
    """
    IT Admin / Auditor: all campaigns.
    Manager / App Owner: campaigns where they have items to review.
    """
    user = get_current_user()

    if user.role in ('it_admin', 'auditor'):
        campaigns = ReviewCampaign.query.order_by(ReviewCampaign.created_at.desc()).all()
    else:
        my_campaign_ids = db.session.query(ReviewItem.campaign_id).filter_by(
            reviewer_id=user.id
        ).distinct().all()
        ids = [cid[0] for cid in my_campaign_ids]
        campaigns = ReviewCampaign.query.filter(ReviewCampaign.id.in_(ids)).order_by(
            ReviewCampaign.created_at.desc()
        ).all()

    result = []
    for c in campaigns:
        all_items = c.items.all()
        total = len(all_items)
        decided = sum(1 for i in all_items if i.decision != 'Pending')
        d = c.to_dict()
        d['total_items'] = total
        d['decided_items'] = decided
        d['completion_pct'] = round(decided / total * 100, 1) if total else 0.0
        result.append(d)

    return jsonify({'campaigns': result}), 200


@campaign_bp.route('/<int:campaign_id>', methods=['GET'])
@require_role('it_admin', 'auditor', 'manager', 'app_owner')
def get_campaign(campaign_id):
    """Get campaign details with items and progress."""
    user = get_current_user()
    campaign = db.session.get(ReviewCampaign, campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    return jsonify({'campaign': _campaign_detail(campaign, user)}), 200


@campaign_bp.route('/<int:campaign_id>/items/<int:item_id>/decide', methods=['POST'])
@require_role('manager', 'app_owner', 'it_admin')
def decide_review_item(campaign_id, item_id):
    """Record a Keep or Revoke decision on a review item."""
    user = get_current_user()
    campaign = db.session.get(ReviewCampaign, campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    if campaign.status != 'Active':
        return jsonify({'error': 'Campaign is not active'}), 400

    item = db.session.get(ReviewItem, item_id)
    if not item or item.campaign_id != campaign_id:
        return jsonify({'error': 'Review item not found'}), 404

    # Only the assigned reviewer (or IT Admin) can decide
    if user.role != 'it_admin' and item.reviewer_id != user.id:
        return jsonify({'error': 'You are not the assigned reviewer for this item'}), 403

    if item.decision != 'Pending':
        return jsonify({'error': 'This item has already been decided'}), 400

    data = request.get_json() or {}
    decision = (data.get('decision') or '').strip()
    comments = (data.get('comments') or '').strip()

    if decision not in ('Keep', 'Revoke'):
        return jsonify({'error': 'decision must be "Keep" or "Revoke"'}), 400

    before = item.to_dict()
    item.decision = decision
    item.comments = comments
    item.decided_at = datetime.utcnow()

    # If revoke decision, flag the grant for IT Admin
    if decision == 'Revoke':
        grant = db.session.get(AccessGrant, item.grant_id)
        if grant and grant.is_active:
            # We flag this by setting a note in the audit log;
            # IT Admin will see it in their fulfilment queue
            db.session.add(AuditLog(
                user_id=user.id,
                action='REVIEW_REVOKE_RECOMMENDED',
                entity_type='AccessGrant',
                entity_id=grant.id,
                before_state=json.dumps({'decision': 'Pending'}),
                after_state=json.dumps({'decision': 'Revoke', 'campaign_id': campaign_id}),
                timestamp=datetime.utcnow(),
            ))

    _log(user.id, 'REVIEW_ITEM_DECIDED', 'ReviewItem', item.id, before=before, after=item.to_dict())

    # Check if campaign is now complete
    all_items = campaign.items.all()
    if all(i.decision != 'Pending' for i in all_items):
        campaign.status = 'Completed'
        _log(user.id, 'CAMPAIGN_COMPLETED', 'ReviewCampaign', campaign.id,
             before={'status': 'Active'}, after={'status': 'Completed'})

    db.session.commit()
    return jsonify({'item': _enrich_item(item)}), 200


@campaign_bp.route('/<int:campaign_id>/cancel', methods=['POST'])
@require_role('it_admin')
def cancel_campaign(campaign_id):
    """Cancel an active campaign. IT Admin only."""
    user = get_current_user()
    campaign = db.session.get(ReviewCampaign, campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    if campaign.status != 'Active':
        return jsonify({'error': 'Only active campaigns can be cancelled'}), 400

    before = campaign.to_dict()
    campaign.status = 'Cancelled'
    _log(user.id, 'CAMPAIGN_CANCELLED', 'ReviewCampaign', campaign.id,
         before=before, after=campaign.to_dict())
    db.session.commit()
    return jsonify({'campaign': campaign.to_dict()}), 200
