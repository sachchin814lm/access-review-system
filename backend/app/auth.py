import secrets
from datetime import datetime
from flask import request, g
import bcrypt

from app import db
from app.models import Session, User


def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(password, password_hash):
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token():
    """Generate a secure random token."""
    return secrets.token_hex(32)


def get_current_user():
    """Get the currently authenticated user from the request token.

    Returns the User object or None if not authenticated.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header[7:].strip()
    if not token:
        return None

    session = Session.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return None

    user = db.session.get(User, session.user_id)
    if not user or not user.is_active:
        return None

    return user
