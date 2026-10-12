import os
from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from config import Config


# Extensions (ONLY ONCE)
db = SQLAlchemy()
migrate = Migrate()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

csrf = CSRFProtect()


def create_app(config_object=Config):

    if os.getenv("VERCEL"):
        app = Flask(__name__, instance_path="/tmp/instance")
    else:
        app = Flask(__name__)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_object(config_object)

    # Vercel + SQLite protection
    if os.getenv("VERCEL") and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        raise RuntimeError(
            "Vercel needs PostgreSQL DATABASE_URL. Configure Neon DATABASE_URL."
        )

    # Secret key check
    if os.getenv("VERCEL"):
        secret = app.config.get("SECRET_KEY")

        if (
            not secret
            or secret == "dev-only-change-me"
            or secret.startswith("replace-with-")
        ):
            raise RuntimeError(
                "Set a strong SECRET_KEY in Vercel environment variables."
            )


    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)


    # Import models after db initialization
    from app import models


    # Register blueprints
    from app.routes import auth, main, records

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(records.bp)


    # CLI commands
    from app.cli import seed_demo, reset_password, create_admin

    app.cli.command("seed-demo")(seed_demo)
    app.cli.command("reset-password")(reset_password)
    app.cli.command("create-admin")(create_admin)


    # Create database tables command
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
        print("Database tables created.")


    # Template filters
    @app.template_filter("currency")
    def currency(value):
        return "₹{:,.2f}".format(value or 0)


    @app.template_filter("datefmt")
    def datefmt(value, fmt="%d %b %Y"):
        return value.strftime(fmt) if value else "—"


    # Global template variables
    @app.context_processor
    def inject_now():
        return {
            "now": datetime.utcnow()
        }


    return app