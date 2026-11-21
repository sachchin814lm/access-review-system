import json
from datetime import datetime
from app import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship('User', remote_side=[id], foreign_keys=[manager_id],
                              backref='direct_reports')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'manager_id': self.manager_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    _access_levels = db.Column('access_levels', db.Text, nullable=False, default='[]')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref='owned_applications', foreign_keys=[owner_id])

    @property
    def access_levels(self):
        return json.loads(self._access_levels)

    @access_levels.setter
    def access_levels(self, value):
        self._access_levels = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'access_levels': self.access_levels,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AccessRequest(db.Model):
    __tablename__ = 'access_request'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    access_level = db.Column(db.String(50), nullable=False)
    justification = db.Column(db.Text, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='Pending Manager Approval')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requester = db.relationship('User', backref='access_requests', foreign_keys=[requester_id])
    application = db.relationship('Application', backref='access_requests')
    approvals = db.relationship('Approval', backref='request', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'application_id': self.application_id,
            'access_level': self.access_level,
            'justification': self.justification,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Approval(db.Model):
    __tablename__ = 'approval'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('access_request.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approval_type = db.Column(db.String(20), nullable=False)
    decision = db.Column(db.String(10), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, default=datetime.utcnow)

    approver = db.relationship('User', backref='approvals')

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'approver_id': self.approver_id,
            'approval_type': self.approval_type,
            'decision': self.decision,
            'comments': self.comments,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
        }


class AccessGrant(db.Model):
    __tablename__ = 'access_grant'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('access_request.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    access_level = db.Column(db.String(50), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoke_reason = db.Column(db.Text, nullable=True)
    revoked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='access_grants')
    application = db.relationship('Application', backref='access_grants')
    granter = db.relationship('User', foreign_keys=[granted_by_id])
    revoker = db.relationship('User', foreign_keys=[revoked_by_id])
    request = db.relationship('AccessRequest', backref=db.backref('grant', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'application_id': self.application_id,
            'access_level': self.access_level,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'granted_by_id': self.granted_by_id,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoke_reason': self.revoke_reason,
            'revoked_by_id': self.revoked_by_id,
            'is_active': self.is_active,
        }


class ReviewCampaign(db.Model):
    __tablename__ = 'review_campaign'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scope = db.Column(db.String(20), nullable=False)
    scope_ref_id = db.Column(db.Integer, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Active')
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='created_campaigns')
    items = db.relationship('ReviewItem', backref='campaign', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scope': self.scope,
            'scope_ref_id': self.scope_ref_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ReviewItem(db.Model):
    __tablename__ = 'review_item'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('review_campaign.id'), nullable=False)
    grant_id = db.Column(db.Integer, db.ForeignKey('access_grant.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    decision = db.Column(db.String(10), nullable=False, default='Pending')
    comments = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    grant = db.relationship('AccessGrant', backref='review_items')
    reviewer = db.relationship('User', backref='review_items')

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'grant_id': self.grant_id,
            'reviewer_id': self.reviewer_id,
            'decision': self.decision,
            'comments': self.comments,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False)
    before_state = db.Column(db.Text, nullable=True)
    after_state = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'before_state': json.loads(self.before_state) if self.before_state else None,
            'after_state': json.loads(self.after_state) if self.after_state else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class Session(db.Model):
    __tablename__ = 'session'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref='sessions')
