import os
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


def create_app(config_object=Config):
    app = Flask(__name__, instance_path="/tmp/instance") if os.getenv("VERCEL") else Flask(__name__)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_object(config_object)
    if os.getenv("VERCEL") and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        raise RuntimeError("Vercel needs a hosted PostgreSQL DATABASE_URL. Add a Neon Postgres integration in Vercel project settings.")
    if os.getenv("VERCEL") and (not app.config["SECRET_KEY"] or app.config["SECRET_KEY"] == "dev-only-change-me" or app.config["SECRET_KEY"].startswith("replace-with-")):
        raise RuntimeError("Set a strong SECRET_KEY in Vercel project environment variables.")
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    from app import models
    from app.routes import auth, main, records
    from app.cli import seed_demo, reset_password, create_admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(records.bp)
    app.cli.command("seed-demo")(seed_demo)
    app.cli.command("reset-password")(reset_password)
    app.cli.command("create-admin")(create_admin)

    @app.template_filter("currency")
    def currency(value):
        return "₹{:,.2f}".format(value or 0)

    @app.template_filter("datefmt")
    def datefmt(value, fmt="%d %b %Y"):
        return value.strftime(fmt) if value else "—"

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    @app.cli.command("init-db")
    def init_db():
        """Create all tables."""
        db.create_all()
        print("Database tables created.")

    return app
