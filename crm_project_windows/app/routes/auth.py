from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, log_activity

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.active and user.check_password(password):
            login_user(user, remember=bool(request.form.get("remember")))
            log_activity(f"{user.name} signed in", user_id=user.id)
            db.session.commit()
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Email or password is incorrect, or this account is inactive.", "danger")
    return render_template("auth/login.html")

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
