from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "app_user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    customers = db.relationship("Customer", backref="assignee", lazy=True)
    leads = db.relationship("Lead", backref="assignee", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    company = db.Column(db.String(140))
    email = db.Column(db.String(160), index=True)
    phone = db.Column(db.String(40))
    address = db.Column(db.Text)
    industry = db.Column(db.String(100))
    customer_type = db.Column(db.String(40), default="Prospect")
    assigned_to = db.Column(db.Integer, db.ForeignKey("app_user.id", ondelete="SET NULL"), index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    leads = db.relationship("Lead", backref="customer", lazy=True)


class Lead(db.Model):
    __tablename__ = "sales_lead"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    company = db.Column(db.String(140))
    email = db.Column(db.String(160))
    phone = db.Column(db.String(40))
    source = db.Column(db.String(80))
    status = db.Column(db.String(30), default="New", nullable=False, index=True)
    priority = db.Column(db.String(20), default="Medium", nullable=False)
    expected_value = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("app_user.id", ondelete="SET NULL"), index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id", ondelete="SET NULL"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, index=True)
    company = db.Column(db.String(140))
    stage = db.Column(db.String(30), default="Prospecting", nullable=False, index=True)
    expected_revenue = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    actual_revenue = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    close_date = db.Column(db.Date)
    lead_id = db.Column(db.Integer, db.ForeignKey("sales_lead.id", ondelete="SET NULL"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("app_user.id", ondelete="SET NULL"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lead = db.relationship("Lead", backref="opportunities")
    assignee = db.relationship("User", foreign_keys=[assigned_to])


class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    followup_type = db.Column(db.String(20), default="Call", nullable=False)
    due_at = db.Column(db.DateTime, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    notes = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id", ondelete="CASCADE"))
    lead_id = db.Column(db.Integer, db.ForeignKey("sales_lead.id", ondelete="CASCADE"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("app_user.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    customer = db.relationship("Customer", backref="followups")
    lead = db.relationship("Lead", backref="followups")
    assignee = db.relationship("User", foreign_keys=[assigned_to])


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(40))
    entity_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = db.relationship("User")


def log_activity(message, entity_type=None, entity_id=None, user_id=None):
    db.session.add(Activity(message=message, entity_type=entity_type, entity_id=entity_id, user_id=user_id))
