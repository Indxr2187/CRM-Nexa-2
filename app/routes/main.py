from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Customer, Lead, Opportunity, FollowUp, Activity, User

bp = Blueprint("main", __name__)

def admin_required():
    if current_user.role != "admin": abort(403)

@bp.get("/")
@login_required
def dashboard():
    total_leads = Lead.query.count()
    converted = Lead.query.filter_by(status="Converted").count()
    statuses = ["New", "Contacted", "Qualified", "Negotiation", "Converted", "Lost"]
    status_counts = [Lead.query.filter_by(status=s).count() for s in statuses]
    stages = ["Prospecting", "Qualification", "Proposal", "Won", "Lost"]
    # SQLAlchemy compiles these dialect-specific date functions per database.
    if db.engine.dialect.name == "postgresql":
        month_expr = func.to_char(Opportunity.created_at, "YYYY-MM")
    else:
        month_expr = func.strftime("%Y-%m", Opportunity.created_at)
    monthly = db.session.query(month_expr, func.sum(Opportunity.actual_revenue)).filter(Opportunity.stage == "Won").group_by(month_expr).order_by(month_expr).all()
    return render_template("dashboard.html", customer_count=Customer.query.count(), lead_count=total_leads,
        active_leads=Lead.query.filter(Lead.status.notin_(["Converted", "Lost"])).count(), converted=converted,
        pending=FollowUp.query.filter_by(completed=False).count(), opportunity_count=Opportunity.query.count(),
        conversion=(round(converted * 100 / total_leads, 1) if total_leads else 0), statuses=statuses, status_counts=status_counts,
        stages=stages, activities=Activity.query.order_by(Activity.created_at.desc()).limit(8).all(),
        followups=FollowUp.query.filter_by(completed=False).order_by(FollowUp.due_at).limit(5).all(),
        revenue_labels=[r[0] or "" for r in monthly], revenue_values=[float(r[1] or 0) for r in monthly])

@bp.get("/pipeline")
@login_required
def pipeline():
    stages = ["Prospecting", "Qualification", "Proposal", "Won", "Lost"]
    return render_template("pipeline.html", stages=stages, opportunities=Opportunity.query.order_by(Opportunity.created_at.desc()).all())

@bp.route("/reports", methods=["GET"])
@login_required
def reports():
    return render_template("reports.html", statuses=["New", "Contacted", "Qualified", "Negotiation", "Converted", "Lost"],
        leads=Lead.query.all(), opportunities=Opportunity.query.all(), users=User.query.filter_by(active=True).all(),
        customers=Customer.query.count(), followups=FollowUp.query.all())

@bp.get("/reports/export.csv")
@login_required
def export_csv():
    import csv, io
    from flask import make_response
    out = io.StringIO(); writer = csv.writer(out)
    writer.writerow(["Name", "Company", "Status", "Priority", "Expected value", "Owner"])
    for lead in Lead.query.order_by(Lead.name): writer.writerow([lead.name, lead.company, lead.status, lead.priority, lead.expected_value, lead.assignee.name if lead.assignee else ""])
    response = make_response(out.getvalue()); response.headers["Content-Type"] = "text/csv"; response.headers["Content-Disposition"] = "attachment; filename=crm-leads.csv"
    return response

@bp.route("/employees", methods=["GET", "POST"])
@login_required
def employees():
    admin_required()
    if request.method == "POST":
        name=request.form.get("name", "").strip(); email=request.form.get("email", "").strip().lower(); password=request.form.get("password", ""); role=request.form.get("role", "employee")
        if not name or "@" not in email or len(password) < 8 or role not in ("admin", "employee") or User.query.filter_by(email=email).first():
            flash("Enter a name, a valid unique email, and a password of at least 8 characters.", "danger")
        else:
            user=User(name=name,email=email,role=role); user.set_password(password); db.session.add(user); db.session.flush()
            from app.models import log_activity
            log_activity(f"Created employee account for {name}", "user", user.id, current_user.id); db.session.commit(); flash("Employee account created.", "success")
        return redirect(url_for("main.employees"))
    return render_template("employees.html", employees=User.query.order_by(User.name).all())

@bp.post("/employees/<int:user_id>/toggle")
@login_required
def toggle_employee(user_id):
    admin_required(); user=User.query.get_or_404(user_id)
    if user.id == current_user.id: flash("You cannot deactivate your own account.", "warning")
    else:
        user.active=not user.active; db.session.commit(); flash("Employee account updated.", "success")
    return redirect(url_for("main.employees"))

@bp.route("/employees/<int:user_id>", methods=["GET", "POST"])
@login_required
def employee_detail(user_id):
    admin_required(); user=User.query.get_or_404(user_id)
    if request.method == "POST":
        name=request.form.get("name", "").strip(); email=request.form.get("email", "").strip().lower(); role=request.form.get("role", "employee")
        duplicate=User.query.filter(User.email==email, User.id!=user.id).first()
        if not name or "@" not in email or duplicate or role not in ("admin", "employee"):
            flash("Enter a name, unique valid email, and valid role.", "danger")
        elif request.form.get("password") and len(request.form["password"]) < 8:
            flash("Password must be at least 8 characters.", "danger")
        else:
            user.name=name; user.email=email; user.role=role
            if request.form.get("password"): user.set_password(request.form["password"])
            db.session.commit(); flash("Employee details updated.", "success")
        return redirect(url_for("main.employee_detail", user_id=user.id))
    activity=Activity.query.filter_by(user_id=user.id).order_by(Activity.created_at.desc()).limit(30).all()
    return render_template("employee_detail.html", employee=user, activity=activity)
