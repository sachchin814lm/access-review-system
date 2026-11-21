from flask import Blueprint, request, jsonify

from app import db
from app.models import AuditLog, User
from app.rbac import require_role

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('', methods=['GET'])
@require_role('auditor', 'it_admin')
def get_audit_log():
    """Search and filter the audit log. Auditor and IT Admin only."""
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 200)

    query = AuditLog.query

    action_filter = request.args.get('action')
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))

    entity_type = request.args.get('entity_type')
    if entity_type:
        query = query.filter_by(entity_type=entity_type)

    user_id = request.args.get('user_id')
    if user_id:
        query = query.filter_by(user_id=int(user_id))

    date_from = request.args.get('date_from')
    if date_from:
        from datetime import datetime
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))

    date_to = request.args.get('date_to')
    if date_to:
        from datetime import datetime
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    result = []
    for log in logs:
        d = log.to_dict()
        d['username'] = log.user.username if log.user else None
        d['user_full_name'] = log.user.full_name if log.user else None
        result.append(d)

    return jsonify({
        'logs': result,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    }), 200
