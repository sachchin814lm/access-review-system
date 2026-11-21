from functools import wraps
from flask import jsonify
from app.auth import get_current_user


def login_required(f):
    """Decorator that requires a valid authenticated session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """Decorator that requires the user to have one of the specified roles.

    Usage:
        @require_role('it_admin', 'auditor')
        def admin_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            if user.role not in roles:
                return jsonify({
                    'error': f'Access denied. Required role(s): {", ".join(roles)}'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
