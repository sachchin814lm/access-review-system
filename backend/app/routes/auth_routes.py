from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from app import db
from app.models import User, Session
from app.auth import check_password, generate_token, get_current_user
from app.rbac import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return a session token."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({'error': 'Invalid username or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    token = generate_token()
    session = Session(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Invalidate the current session token."""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header[7:]
    Session.query.filter_by(token=token).delete()
    db.session.commit()
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    """Return the currently authenticated user's profile."""
    user = get_current_user()
    return jsonify({'user': user.to_dict()}), 200
