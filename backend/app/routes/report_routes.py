import csv
import io
from datetime import date
from flask import Blueprint, request, jsonify, Response

from app import db
from app.models import AccessGrant, AccessRequest, ReviewItem, ReviewCampaign, User, Application
from app.rbac import require_role

report_bp = Blueprint('reports', __name__)


def _csv_response(rows, headers, filename):
    """Return a CSV download response."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


def _want_csv():
    return request.args.get('format', '').lower() == 'csv'


@report_bp.route('/access-by-user', methods=['GET'])
@require_role('it_admin', 'auditor')
def access_by_user():
    """Active grants grouped by user."""
    grants = AccessGrant.query.filter_by(is_active=True).all()
    rows = []
    for g in grants:
        rows.append({
            'user_id': g.user_id,
            'user_name': g.user.full_name if g.user else '',
            'username': g.user.username if g.user else '',
            'application': g.application.name if g.application else '',
            'access_level': g.access_level,
            'granted_at': g.granted_at.isoformat() if g.granted_at else '',
        })
    rows.sort(key=lambda r: r['user_name'])

    if _want_csv():
        return _csv_response(rows,
            ['user_id', 'user_name', 'username', 'application', 'access_level', 'granted_at'],
            'access_by_user.csv')
    return jsonify({'report': 'access_by_user', 'rows': rows, 'total': len(rows)}), 200


@report_bp.route('/access-by-application', methods=['GET'])
@require_role('it_admin', 'auditor')
def access_by_application():
    """Active grants grouped by application."""
    grants = AccessGrant.query.filter_by(is_active=True).all()
    rows = []
    for g in grants:
        rows.append({
            'application_id': g.application_id,
            'application': g.application.name if g.application else '',
            'user_name': g.user.full_name if g.user else '',
            'username': g.user.username if g.user else '',
            'access_level': g.access_level,
            'granted_at': g.granted_at.isoformat() if g.granted_at else '',
        })
    rows.sort(key=lambda r: r['application'])

    if _want_csv():
        return _csv_response(rows,
            ['application_id', 'application', 'user_name', 'username', 'access_level', 'granted_at'],
            'access_by_application.csv')
    return jsonify({'report': 'access_by_application', 'rows': rows, 'total': len(rows)}), 200


@report_bp.route('/pending-approvals', methods=['GET'])
@require_role('it_admin', 'auditor')
def pending_approvals():
    """All requests in pending approval states."""
    reqs = AccessRequest.query.filter(
        AccessRequest.status.in_(['Pending Manager Approval', 'Pending Owner Approval'])
    ).all()
    rows = []
    for r in reqs:
        rows.append({
            'request_id': r.id,
            'requester': r.requester.full_name if r.requester else '',
            'application': r.application.name if r.application else '',
            'access_level': r.access_level,
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else '',
            'justification': r.justification,
        })

    if _want_csv():
        return _csv_response(rows,
            ['request_id', 'requester', 'application', 'access_level', 'status', 'created_at', 'justification'],
            'pending_approvals.csv')
    return jsonify({'report': 'pending_approvals', 'rows': rows, 'total': len(rows)}), 200


@report_bp.route('/overdue-reviews', methods=['GET'])
@require_role('it_admin', 'auditor')
def overdue_reviews():
    """Review items past their campaign due date still pending."""
    today = date.today()
    items = db.session.query(ReviewItem).join(ReviewCampaign).filter(
        ReviewItem.decision == 'Pending',
        ReviewCampaign.due_date < today,
        ReviewCampaign.status == 'Active',
    ).all()

    rows = []
    for item in items:
        rows.append({
            'campaign_id': item.campaign_id,
            'campaign_name': item.campaign.name if item.campaign else '',
            'due_date': item.campaign.due_date.isoformat() if item.campaign else '',
            'reviewer': item.reviewer.full_name if item.reviewer else '',
            'user_name': item.grant.user.full_name if item.grant and item.grant.user else '',
            'application': item.grant.application.name if item.grant and item.grant.application else '',
            'access_level': item.grant.access_level if item.grant else '',
        })

    if _want_csv():
        return _csv_response(rows,
            ['campaign_id', 'campaign_name', 'due_date', 'reviewer', 'user_name', 'application', 'access_level'],
            'overdue_reviews.csv')
    return jsonify({'report': 'overdue_reviews', 'rows': rows, 'total': len(rows)}), 200


@report_bp.route('/revoked-access', methods=['GET'])
@require_role('it_admin', 'auditor')
def revoked_access():
    """All revoked grants with reasons and dates."""
    grants = AccessGrant.query.filter_by(is_active=False).all()
    rows = []
    for g in grants:
        rows.append({
            'grant_id': g.id,
            'user_name': g.user.full_name if g.user else '',
            'application': g.application.name if g.application else '',
            'access_level': g.access_level,
            'granted_at': g.granted_at.isoformat() if g.granted_at else '',
            'revoked_at': g.revoked_at.isoformat() if g.revoked_at else '',
            'revoke_reason': g.revoke_reason or '',
            'revoked_by': g.revoker.full_name if g.revoker else '',
        })

    if _want_csv():
        return _csv_response(rows,
            ['grant_id', 'user_name', 'application', 'access_level', 'granted_at', 'revoked_at', 'revoke_reason', 'revoked_by'],
            'revoked_access.csv')
    return jsonify({'report': 'revoked_access', 'rows': rows, 'total': len(rows)}), 200


@report_bp.route('/campaign-results', methods=['GET'])
@require_role('it_admin', 'auditor')
def campaign_results():
    """Summary and item details for a specific campaign."""
    campaign_id = request.args.get('campaign_id')
    if not campaign_id:
        return jsonify({'error': 'campaign_id query param is required'}), 400

    campaign = db.session.get(ReviewCampaign, int(campaign_id))
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    all_items = campaign.items.all()
    rows = []
    for item in all_items:
        rows.append({
            'campaign': campaign.name,
            'due_date': campaign.due_date.isoformat(),
            'reviewer': item.reviewer.full_name if item.reviewer else '',
            'user_name': item.grant.user.full_name if item.grant and item.grant.user else '',
            'application': item.grant.application.name if item.grant and item.grant.application else '',
            'access_level': item.grant.access_level if item.grant else '',
            'decision': item.decision,
            'comments': item.comments or '',
            'decided_at': item.decided_at.isoformat() if item.decided_at else '',
        })

    total = len(rows)
    keep = sum(1 for r in rows if r['decision'] == 'Keep')
    revoke = sum(1 for r in rows if r['decision'] == 'Revoke')
    pending = sum(1 for r in rows if r['decision'] == 'Pending')

    if _want_csv():
        return _csv_response(rows,
            ['campaign', 'due_date', 'reviewer', 'user_name', 'application', 'access_level', 'decision', 'comments', 'decided_at'],
            f'campaign_{campaign_id}_results.csv')

    return jsonify({
        'report': 'campaign_results',
        'campaign': campaign.to_dict(),
        'summary': {'total': total, 'keep': keep, 'revoke': revoke, 'pending': pending},
        'rows': rows,
    }), 200
