import json
from datetime import datetime
from flask import Blueprint, request, jsonify

from app import db
from app.auth import get_current_user
from app.models import (
    AccessRequest, Application, Approval, AuditLog, User
)
from app.rbac import login_required, require_role

request_bp = Blueprint('requests', __name__)


def _log(user_id, action, entity_id, before=None, after=None):
    db.session.add(AuditLog(
        user_id=user_id,
        action=action,
        entity_type='AccessRequest',
        entity_id=entity_id,
        before_state=json.dumps(before) if before else None,
        after_state=json.dumps(after) if after else None,
        timestamp=datetime.utcnow(),
    ))


@request_bp.route('', methods=['POST'])
@require_role('employee', 'manager', 'app_owner')
def create_request():
    """Submit a new access request. Employees (and managers/owners acting as employees) only."""
    user = get_current_user()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    app_id = data.get('application_id')
    access_level = (data.get('access_level') or '').strip()
    justification = (data.get('justification') or '').strip()
    expiry_date_str = data.get('expiry_date')

    if not app_id:
        return jsonify({'error': 'application_id is required'}), 400
    if not access_level:
        return jsonify({'error': 'access_level is required'}), 400
    if not justification:
        return jsonify({'error': 'justification is required'}), 400

    application = db.session.get(Application, app_id)
    if not application or not application.is_active:
        return jsonify({'error': 'Application not found'}), 404

    if access_level not in application.access_levels:
        return jsonify({
            'error': f'Invalid access_level. Valid options: {application.access_levels}'
        }), 400

    expiry_date = None
    if expiry_date_str:
        try:
            from datetime import date
            expiry_date = date.fromisoformat(expiry_date_str)
        except ValueError:
            return jsonify({'error': 'expiry_date must be YYYY-MM-DD'}), 400

    # Check requester has a manager
    if not user.manager_id:
        return jsonify({'error': 'You must have a manager assigned before submitting requests'}), 400

    req = AccessRequest(
        requester_id=user.id,
        application_id=app_id,
        access_level=access_level,
        justification=justification,
        expiry_date=expiry_date,
        status='Pending Manager Approval',
    )
    db.session.add(req)
    db.session.flush()
    _log(user.id, 'REQUEST_CREATED', req.id, after=req.to_dict())
    db.session.commit()
    return jsonify({'request': req.to_dict()}), 201


@request_bp.route('/mine', methods=['GET'])
@login_required
def my_requests():
    """Return the current user's own access requests."""
    user = get_current_user()
    reqs = AccessRequest.query.filter_by(requester_id=user.id).order_by(
        AccessRequest.created_at.desc()
    ).all()

    result = []
    for r in reqs:
        d = r.to_dict()
        d['application_name'] = r.application.name if r.application else None
        d['approvals'] = [a.to_dict() for a in r.approvals]
        result.append(d)

    return jsonify({'requests': result}), 200


@request_bp.route('', methods=['GET'])
@require_role('it_admin', 'auditor')
def list_all_requests():
    """List all requests. IT Admin / Auditor only."""
    status_filter = request.args.get('status')
    query = AccessRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    reqs = query.order_by(AccessRequest.created_at.desc()).all()

    result = []
    for r in reqs:
        d = r.to_dict()
        d['application_name'] = r.application.name if r.application else None
        d['requester_name'] = r.requester.full_name if r.requester else None
        d['approvals'] = [a.to_dict() for a in r.approvals]
        result.append(d)

    return jsonify({'requests': result}), 200


@request_bp.route('/pending', methods=['GET'])
@require_role('manager', 'app_owner', 'it_admin')
def pending_approvals():
    """
    Manager: requests from direct reports at 'Pending Manager Approval'.
    App Owner: requests for owned apps at 'Pending Owner Approval'.
    IT Admin: all pending requests.
    """
    user = get_current_user()

    if user.role == 'manager':
        report_ids = [u.id for u in user.direct_reports]
        reqs = AccessRequest.query.filter(
            AccessRequest.requester_id.in_(report_ids),
            AccessRequest.status == 'Pending Manager Approval'
        ).order_by(AccessRequest.created_at.asc()).all()

    elif user.role == 'app_owner':
        owned_app_ids = [a.id for a in user.owned_applications]
        reqs = AccessRequest.query.filter(
            AccessRequest.application_id.in_(owned_app_ids),
            AccessRequest.status == 'Pending Owner Approval'
        ).order_by(AccessRequest.created_at.asc()).all()

    else:  # it_admin
        reqs = AccessRequest.query.filter(
            AccessRequest.status.in_(['Pending Manager Approval', 'Pending Owner Approval'])
        ).order_by(AccessRequest.created_at.asc()).all()

    result = []
    for r in reqs:
        d = r.to_dict()
        d['application_name'] = r.application.name if r.application else None
        d['requester_name'] = r.requester.full_name if r.requester else None
        d['approvals'] = [a.to_dict() for a in r.approvals]
        result.append(d)

    return jsonify({'requests': result}), 200


@request_bp.route('/<int:req_id>', methods=['GET'])
@login_required
def get_request(req_id):
    """Get a single request. Employees see own only; admins/auditors see all."""
    user = get_current_user()
    req = db.session.get(AccessRequest, req_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    if user.role not in ('it_admin', 'auditor', 'manager', 'app_owner'):
        if req.requester_id != user.id:
            return jsonify({'error': 'Access denied'}), 403

    d = req.to_dict()
    d['application_name'] = req.application.name if req.application else None
    d['requester_name'] = req.requester.full_name if req.requester else None
    d['approvals'] = [a.to_dict() for a in req.approvals]
    return jsonify({'request': d}), 200


@request_bp.route('/<int:req_id>/approve', methods=['POST'])
@require_role('manager', 'app_owner')
def approve_request(req_id):
    """Approve a request. Manager approves manager-stage; Owner approves owner-stage."""
    user = get_current_user()
    req = db.session.get(AccessRequest, req_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    data = request.get_json() or {}
    comments = (data.get('comments') or '').strip()
    before = req.to_dict()

    if user.role == 'manager':
        if req.status != 'Pending Manager Approval':
            return jsonify({'error': 'Request is not pending manager approval'}), 400
        # Must be from a direct report
        report_ids = [u.id for u in user.direct_reports]
        if req.requester_id not in report_ids:
            return jsonify({'error': 'This request is not from one of your direct reports'}), 403
        req.status = 'Pending Owner Approval'
        approval_type = 'manager'

    elif user.role == 'app_owner':
        if req.status != 'Pending Owner Approval':
            return jsonify({'error': 'Request is not pending owner approval'}), 400
        # Must own the application
        owned_ids = [a.id for a in user.owned_applications]
        if req.application_id not in owned_ids:
            return jsonify({'error': 'You do not own this application'}), 403
        req.status = 'Approved'
        approval_type = 'app_owner'

    req.updated_at = datetime.utcnow()
    approval = Approval(
        request_id=req.id,
        approver_id=user.id,
        approval_type=approval_type,
        decision='approved',
        comments=comments,
    )
    db.session.add(approval)

    action = 'MANAGER_APPROVED' if approval_type == 'manager' else 'OWNER_APPROVED'
    _log(user.id, action, req.id, before=before, after=req.to_dict())
    db.session.commit()

    return jsonify({'request': req.to_dict(), 'approval': approval.to_dict()}), 200


@request_bp.route('/<int:req_id>/reject', methods=['POST'])
@require_role('manager', 'app_owner')
def reject_request(req_id):
    """Reject a request. Manager or Owner can reject at their respective stage."""
    user = get_current_user()
    req = db.session.get(AccessRequest, req_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    data = request.get_json() or {}
    comments = (data.get('comments') or '').strip()
    before = req.to_dict()

    if user.role == 'manager':
        if req.status != 'Pending Manager Approval':
            return jsonify({'error': 'Request is not pending manager approval'}), 400
        report_ids = [u.id for u in user.direct_reports]
        if req.requester_id not in report_ids:
            return jsonify({'error': 'This request is not from one of your direct reports'}), 403
        approval_type = 'manager'

    elif user.role == 'app_owner':
        if req.status != 'Pending Owner Approval':
            return jsonify({'error': 'Request is not pending owner approval'}), 400
        owned_ids = [a.id for a in user.owned_applications]
        if req.application_id not in owned_ids:
            return jsonify({'error': 'You do not own this application'}), 403
        approval_type = 'app_owner'

    req.status = 'Rejected'
    req.updated_at = datetime.utcnow()

    approval = Approval(
        request_id=req.id,
        approver_id=user.id,
        approval_type=approval_type,
        decision='rejected',
        comments=comments,
    )
    db.session.add(approval)

    action = 'MANAGER_REJECTED' if approval_type == 'manager' else 'OWNER_REJECTED'
    _log(user.id, action, req.id, before=before, after=req.to_dict())
    db.session.commit()

    return jsonify({'request': req.to_dict(), 'approval': approval.to_dict()}), 200
