import json
from datetime import datetime
from flask import Blueprint, request, jsonify

from app import db
from app.auth import get_current_user
from app.models import AccessRequest, AccessGrant, AuditLog
from app.rbac import require_role

fulfil_bp = Blueprint('fulfilment', __name__)


def _log(user_id, action, entity_id, before=None, after=None):
    db.session.add(AuditLog(
        user_id=user_id,
        action=action,
        entity_type='AccessGrant',
        entity_id=entity_id,
        before_state=json.dumps(before) if before else None,
        after_state=json.dumps(after) if after else None,
        timestamp=datetime.utcnow(),
    ))


@fulfil_bp.route('', methods=['GET'])
@require_role('it_admin', 'auditor')
def list_grants():
    """List all access grants. IT Admin / Auditor only."""
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    pending_revoke = request.args.get('pending_revoke', 'false').lower() == 'true'

    query = AccessGrant.query
    if active_only:
        query = query.filter_by(is_active=True)
    if pending_revoke:
        query = query.filter_by(is_active=True, pending_revoke=True)

    grants = query.order_by(AccessGrant.granted_at.desc()).all()

    result = []
    for g in grants:
        d = g.to_dict()
        d['user_name'] = g.user.full_name if g.user else None
        d['application_name'] = g.application.name if g.application else None
        result.append(d)

    return jsonify({'grants': result}), 200


@fulfil_bp.route('/approved', methods=['GET'])
@require_role('it_admin')
def list_approved_requests():
    """List approved requests not yet granted. IT Admin only."""
    reqs = AccessRequest.query.filter_by(status='Approved').order_by(
        AccessRequest.updated_at.asc()
    ).all()

    result = []
    for r in reqs:
        d = r.to_dict()
        d['application_name'] = r.application.name if r.application else None
        d['requester_name'] = r.requester.full_name if r.requester else None
        result.append(d)

    return jsonify({'requests': result}), 200


@fulfil_bp.route('', methods=['POST'])
@require_role('it_admin')
def grant_access():
    """Grant access for an approved request. IT Admin only."""
    user = get_current_user()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    req_id = data.get('request_id')
    if not req_id:
        return jsonify({'error': 'request_id is required'}), 400

    req = db.session.get(AccessRequest, req_id)
    if not req:
        return jsonify({'error': 'Access request not found'}), 404

    if req.grant or req.status == 'Granted':
        return jsonify({'error': 'Access has already been granted for this request'}), 409

    if req.status != 'Approved':
        return jsonify({
            'error': f'Request must be in Approved status to grant. Current: {req.status}'
        }), 400

    before_req = req.to_dict()
    req.status = 'Granted'
    req.updated_at = datetime.utcnow()

    grant = AccessGrant(
        request_id=req.id,
        user_id=req.requester_id,
        application_id=req.application_id,
        access_level=req.access_level,
        granted_at=datetime.utcnow(),
        granted_by_id=user.id,
        is_active=True,
    )
    db.session.add(grant)
    db.session.flush()

    # Log the request status change
    db.session.add(AuditLog(
        user_id=user.id,
        action='ACCESS_GRANTED',
        entity_type='AccessGrant',
        entity_id=grant.id,
        before_state=json.dumps(before_req),
        after_state=json.dumps(grant.to_dict()),
        timestamp=datetime.utcnow(),
    ))
    db.session.commit()

    d = grant.to_dict()
    d['user_name'] = grant.user.full_name if grant.user else None
    d['application_name'] = grant.application.name if grant.application else None
    return jsonify({'grant': d}), 201


@fulfil_bp.route('/<int:grant_id>/revoke', methods=['PATCH'])
@require_role('it_admin')
def revoke_access(grant_id):
    """Revoke an active access grant. IT Admin only."""
    user = get_current_user()
    grant = db.session.get(AccessGrant, grant_id)
    if not grant:
        return jsonify({'error': 'Access grant not found'}), 404

    if not grant.is_active:
        return jsonify({'error': 'Access has already been revoked'}), 400

    data = request.get_json() or {}
    revoke_reason = (data.get('revoke_reason') or '').strip()
    if not revoke_reason:
        return jsonify({'error': 'revoke_reason is required'}), 400

    before = grant.to_dict()
    grant.is_active = False
    grant.revoked_at = datetime.utcnow()
    grant.revoke_reason = revoke_reason
    grant.revoked_by_id = user.id

    # Update the original request status to Revoked
    if grant.request_id:
        req = db.session.get(AccessRequest, grant.request_id)
        if req:
            req.status = 'Revoked'
            req.updated_at = datetime.utcnow()

    _log(user.id, 'ACCESS_REVOKED', grant.id, before=before, after=grant.to_dict())
    db.session.commit()

    return jsonify({'grant': grant.to_dict()}), 200
