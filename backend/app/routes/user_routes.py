from flask import Blueprint, request, jsonify

from app import db
from app.models import User
from app.auth import hash_password
from app.rbac import require_role

user_bp = Blueprint('users', __name__)

VALID_ROLES = ['employee', 'manager', 'app_owner', 'it_admin', 'auditor']


@user_bp.route('', methods=['GET'])
@require_role('it_admin', 'auditor')
def list_users():
    """List all users. IT Admin and Auditor only."""
    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@user_bp.route('/<int:user_id>', methods=['GET'])
@require_role('it_admin', 'auditor')
def get_user(user_id):
    """Get a single user by ID. IT Admin and Auditor only."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('', methods=['POST'])
@require_role('it_admin')
def create_user():
    """Create a new user. IT Admin only."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['username', 'email', 'password', 'full_name', 'role']
    for field in required:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            return jsonify({'error': f'{field} is required'}), 400

    if data['role'] not in VALID_ROLES:
        return jsonify({
            'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'
        }), 400

    if User.query.filter_by(username=data['username'].strip()).first():
        return jsonify({'error': 'Username already exists'}), 409

    user = User(
        username=data['username'].strip(),
        email=data['email'].strip(),
        password_hash=hash_password(data['password']),
        full_name=data['full_name'].strip(),
        role=data['role'],
        manager_id=data.get('manager_id'),
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'user': user.to_dict()}), 201


@user_bp.route('/<int:user_id>', methods=['PUT'])
@require_role('it_admin')
def update_user(user_id):
    """Update an existing user. IT Admin only."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'email' in data:
        user.email = data['email'].strip()
    if 'full_name' in data:
        user.full_name = data['full_name'].strip()
    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return jsonify({
                'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'
            }), 400
        user.role = data['role']
    if 'manager_id' in data:
        user.manager_id = data['manager_id']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data and data['password']:
        user.password_hash = hash_password(data['password'])

    db.session.commit()
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@require_role('it_admin')
def delete_user(user_id):
    """Deactivate a user (soft delete). IT Admin only."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.is_active = False
    db.session.commit()
    return jsonify({'message': 'User deactivated successfully'}), 200
