from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class:
        app.config.from_object(config_class)
    else:
        from .config import Config
        app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

    from .routes.auth_routes import auth_bp
    from .routes.user_routes import user_bp
    from .routes.app_routes import app_bp
    from .routes.request_routes import request_bp
    from .routes.fulfil_routes import fulfil_bp
    from .routes.campaign_routes import campaign_bp
    from .routes.audit_routes import audit_bp
    from .routes.report_routes import report_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(app_bp, url_prefix='/api/applications')
    app.register_blueprint(request_bp, url_prefix='/api/requests')
    app.register_blueprint(fulfil_bp, url_prefix='/api/fulfilment')
    app.register_blueprint(campaign_bp, url_prefix='/api/campaigns')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(report_bp, url_prefix='/api/reports')

    with app.app_context():
        import os
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:///:memory:'):
            file_path = db_uri.replace('sqlite:///', '')
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        db.create_all()

    return app
