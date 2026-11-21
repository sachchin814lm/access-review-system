from flask import Blueprint, request, jsonify

from app import db
from app.models import Application, User
from app.rbac import require_role, login_required

app_bp = Blueprint('applications', __name__)


@app_bp.route('', methods=['GET'])
@login_required
def list_applications():
    """List all active applications. Any authenticated user."""
    apps = Application.query.filter_by(is_active=True).all()
    return jsonify({'applications': [a.to_dict() for a in apps]}), 200


@app_bp.route('/<int:app_id>', methods=['GET'])
@login_required
def get_application(app_id):
    """Get a single application by ID. Any authenticated user."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    return jsonify({'application': application.to_dict()}), 200


@app_bp.route('', methods=['POST'])
@require_role('it_admin')
def create_application():
    """Create a new application. IT Admin only."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['name', 'owner_id', 'access_levels']
    for field in required:
        if field not in data or (isinstance(data[field], str) and not data[field].strip()):
            return jsonify({'error': f'{field} is required'}), 400

    if not isinstance(data['access_levels'], list) or len(data['access_levels']) == 0:
        return jsonify({'error': 'access_levels must be a non-empty list'}), 400

    owner = db.session.get(User, data['owner_id'])
    if not owner:
        return jsonify({'error': 'Owner user not found'}), 404

    if Application.query.filter_by(name=data['name'].strip()).first():
        return jsonify({'error': 'Application name already exists'}), 409

    application = Application(
        name=data['name'].strip(),
        description=data.get('description', '').strip(),
        owner_id=data['owner_id'],
        is_active=True,
    )
    application.access_levels = data['access_levels']
    db.session.add(application)
    db.session.commit()

    return jsonify({'application': application.to_dict()}), 201


@app_bp.route('/<int:app_id>', methods=['PUT'])
@require_role('it_admin')
def update_application(app_id):
    """Update an existing application. IT Admin only."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'name' in data:
        existing = Application.query.filter_by(name=data['name'].strip()).first()
        if existing and existing.id != app_id:
            return jsonify({'error': 'Application name already exists'}), 409
        application.name = data['name'].strip()
    if 'description' in data:
        application.description = data['description'].strip()
    if 'owner_id' in data:
        owner = db.session.get(User, data['owner_id'])
        if not owner:
            return jsonify({'error': 'Owner user not found'}), 404
        application.owner_id = data['owner_id']
    if 'access_levels' in data:
        if not isinstance(data['access_levels'], list) or len(data['access_levels']) == 0:
            return jsonify({'error': 'access_levels must be a non-empty list'}), 400
        application.access_levels = data['access_levels']
    if 'is_active' in data:
        application.is_active = data['is_active']

    db.session.commit()
    return jsonify({'application': application.to_dict()}), 200


@app_bp.route('/<int:app_id>', methods=['DELETE'])
@require_role('it_admin')
def delete_application(app_id):
    """Deactivate an application (soft delete). IT Admin only."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404

    application.is_active = False
    db.session.commit()
    return jsonify({'message': 'Application deactivated successfully'}), 200
