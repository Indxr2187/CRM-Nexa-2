from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Customer, Lead, Opportunity, FollowUp, User, log_activity

bp = Blueprint("records", __name__)
STATUSES = ["New", "Contacted", "Qualified", "Negotiation", "Converted", "Lost"]
STAGES = ["Prospecting", "Qualification", "Proposal", "Won", "Lost"]

def decimal_value(value):
    try:
        n = Decimal(value or "0")
        if n < 0: raise InvalidOperation
        return n
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid non-negative amount.")

def employees(): return User.query.filter_by(active=True).order_by(User.name).all()

@bp.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    if request.method == "POST":
        name=request.form.get("name", "").strip(); email=request.form.get("email", "").strip() or None
        if not name: flash("Customer name is required.", "danger")
        else:
            c=Customer(name=name,company=request.form.get("company", "").strip(),email=email,phone=request.form.get("phone", "").strip(),address=request.form.get("address", "").strip(),industry=request.form.get("industry", "").strip(),customer_type=request.form.get("customer_type", "Prospect"),assigned_to=request.form.get("assigned_to", type=int) or current_user.id,notes=request.form.get("notes", "").strip())
            db.session.add(c); db.session.flush(); log_activity(f"Added customer {c.name}", "customer", c.id, current_user.id); db.session.commit(); flash("Customer added.", "success")
        return redirect(url_for("records.customers"))
    q=Customer.query
    term=request.args.get("q", "").strip()
    if term: q=q.filter(db.or_(Customer.name.ilike(f"%{term}%"), Customer.company.ilike(f"%{term}%"), Customer.email.ilike(f"%{term}%")))
    if request.args.get("type"): q=q.filter_by(customer_type=request.args["type"])
    sort=request.args.get("sort", "created_at"); col=getattr(Customer, sort, Customer.created_at)
    q=q.order_by(col.desc() if request.args.get("direction", "desc")=="desc" else col.asc())
    return render_template("customers.html", customers=q.all(), employees=employees())

@bp.route("/customers/<int:record_id>", methods=["GET", "POST"])
@login_required
def customer_detail(record_id):
    c=Customer.query.get_or_404(record_id)
    if request.method == "POST":
        c.name=request.form.get("name", "").strip(); c.company=request.form.get("company", "").strip(); c.email=request.form.get("email", "").strip() or None; c.phone=request.form.get("phone", "").strip(); c.address=request.form.get("address", "").strip(); c.industry=request.form.get("industry", "").strip(); c.customer_type=request.form.get("customer_type", "Prospect"); c.assigned_to=request.form.get("assigned_to", type=int); c.notes=request.form.get("notes", "").strip()
        if not c.name: flash("Customer name is required.", "danger")
        else: log_activity(f"Updated customer {c.name}", "customer", c.id, current_user.id); db.session.commit(); flash("Customer updated.", "success")
        return redirect(url_for("records.customer_detail", record_id=c.id))
    return render_template("customer_detail.html", customer=c, employees=employees())

@bp.post("/customers/<int:record_id>/delete")
@login_required
def customer_delete(record_id):
    c=Customer.query.get_or_404(record_id); name=c.name; db.session.delete(c); log_activity(f"Deleted customer {name}", "customer", record_id, current_user.id); db.session.commit(); flash("Customer deleted.", "success"); return redirect(url_for("records.customers"))

@bp.route("/leads", methods=["GET", "POST"])
@login_required
def leads():
    if request.method == "POST":
        name=request.form.get("name", "").strip()
        try: value=decimal_value(request.form.get("expected_value"))
        except ValueError as e: flash(str(e), "danger"); return redirect(url_for("records.leads"))
        if not name: flash("Lead name is required.", "danger")
        else:
            lead=Lead(name=name,company=request.form.get("company", "").strip(),email=request.form.get("email", "").strip(),phone=request.form.get("phone", "").strip(),source=request.form.get("source", "").strip(),status=request.form.get("status", "New"),priority=request.form.get("priority", "Medium"),expected_value=value,assigned_to=request.form.get("assigned_to", type=int) or current_user.id,notes=request.form.get("notes", "").strip())
            if lead.status not in STATUSES: lead.status="New"
            db.session.add(lead); db.session.flush(); log_activity(f"Created lead {lead.name}", "lead", lead.id, current_user.id); db.session.commit(); flash("Lead added.", "success")
        return redirect(url_for("records.leads"))
    q=Lead.query; term=request.args.get("q", "").strip()
    if term: q=q.filter(db.or_(Lead.name.ilike(f"%{term}%"), Lead.company.ilike(f"%{term}%"), Lead.email.ilike(f"%{term}%")))
    if request.args.get("status"): q=q.filter_by(status=request.args["status"])
    if request.args.get("priority"): q=q.filter_by(priority=request.args["priority"])
    return render_template("leads.html", leads=q.order_by(Lead.created_at.desc()).all(), employees=employees(), statuses=STATUSES)

@bp.route("/leads/<int:record_id>", methods=["GET", "POST"])
@login_required
def lead_detail(record_id):
    lead=Lead.query.get_or_404(record_id)
    if request.method == "POST":
        try: value=decimal_value(request.form.get("expected_value"))
        except ValueError as e: flash(str(e), "danger"); return redirect(url_for("records.lead_detail", record_id=lead.id))
        lead.name=request.form.get("name", "").strip(); lead.company=request.form.get("company", "").strip(); lead.email=request.form.get("email", "").strip(); lead.phone=request.form.get("phone", "").strip(); lead.source=request.form.get("source", "").strip(); lead.status=request.form.get("status", "New"); lead.priority=request.form.get("priority", "Medium"); lead.expected_value=value; lead.assigned_to=request.form.get("assigned_to", type=int); lead.notes=request.form.get("notes", "").strip()
        if not lead.name or lead.status not in STATUSES: flash("Enter a name and valid status.", "danger")
        else: log_activity(f"Updated lead {lead.name}", "lead", lead.id, current_user.id); db.session.commit(); flash("Lead updated.", "success")
        return redirect(url_for("records.lead_detail", record_id=lead.id))
    return render_template("lead_detail.html", lead=lead, employees=employees(), statuses=STATUSES)

@bp.route("/opportunities", methods=["GET", "POST"])
@login_required
def opportunities():
    if request.method == "POST":
        try: revenue=decimal_value(request.form.get("expected_revenue")); actual=decimal_value(request.form.get("actual_revenue"))
        except ValueError as e: flash(str(e), "danger"); return redirect(url_for("records.opportunities"))
        name=request.form.get("name", "").strip()
        if not name: flash("Opportunity name is required.", "danger")
        else:
            opp=Opportunity(name=name,company=request.form.get("company", "").strip(),stage=request.form.get("stage", "Prospecting"),expected_revenue=revenue,actual_revenue=actual,close_date=datetime.strptime(request.form["close_date"], "%Y-%m-%d").date() if request.form.get("close_date") else None,lead_id=request.form.get("lead_id", type=int) or None,assigned_to=request.form.get("assigned_to", type=int) or current_user.id,notes=request.form.get("notes", "").strip())
            if opp.stage not in STAGES: opp.stage="Prospecting"
            db.session.add(opp); db.session.flush(); log_activity(f"Created opportunity {opp.name}", "opportunity", opp.id, current_user.id); db.session.commit(); flash("Opportunity added.", "success")
        return redirect(url_for("records.opportunities"))
    return render_template("opportunities.html", opportunities=Opportunity.query.order_by(Opportunity.created_at.desc()).all(), stages=STAGES, leads=Lead.query.order_by(Lead.name).all(), employees=employees())

@bp.post("/opportunities/<int:record_id>/stage")
@login_required
def opportunity_stage(record_id):
    opp=Opportunity.query.get_or_404(record_id); stage=request.form.get("stage")
    if stage not in STAGES: abort(400)
    opp.stage=stage
    if stage != "Won": opp.actual_revenue=0
    log_activity(f"Moved opportunity {opp.name} to {stage}", "opportunity", opp.id, current_user.id); db.session.commit(); flash("Opportunity stage updated.", "success"); return redirect(request.referrer or url_for("main.pipeline"))

@bp.get("/opportunities/<int:record_id>")
@login_required
def opportunity_detail(record_id):
    return render_template("opportunity_detail.html", opportunity=Opportunity.query.get_or_404(record_id), stages=STAGES)

@bp.route("/followups", methods=["GET", "POST"])
@login_required
def followups():
    if request.method == "POST":
        try: due=datetime.fromisoformat(request.form.get("due_at", ""))
        except ValueError: flash("Enter a valid follow-up date and time.", "danger"); return redirect(url_for("records.followups"))
        title=request.form.get("title", "").strip()
        if not title: flash("Follow-up title is required.", "danger")
        else:
            f=FollowUp(title=title,followup_type=request.form.get("followup_type", "Call"),due_at=due,notes=request.form.get("notes", "").strip(),customer_id=request.form.get("customer_id", type=int) or None,lead_id=request.form.get("lead_id", type=int) or None,assigned_to=request.form.get("assigned_to", type=int) or current_user.id)
            db.session.add(f); db.session.flush(); log_activity(f"Scheduled follow-up: {f.title}", "followup", f.id, current_user.id); db.session.commit(); flash("Follow-up scheduled.", "success")
        return redirect(url_for("records.followups"))
    query=FollowUp.query; view=request.args.get("view", "pending")
    if view == "completed": query=query.filter_by(completed=True)
    elif view == "overdue": query=query.filter(FollowUp.completed.is_(False), FollowUp.due_at < datetime.utcnow())
    else: query=query.filter_by(completed=False)
    return render_template("followups.html", followups=query.order_by(FollowUp.due_at).all(), view=view, customers=Customer.query.order_by(Customer.name).all(), leads=Lead.query.order_by(Lead.name).all(), employees=employees())

@bp.post("/followups/<int:record_id>/complete")
@login_required
def followup_complete(record_id):
    f=FollowUp.query.get_or_404(record_id); f.completed=not f.completed; log_activity(f"{'Completed' if f.completed else 'Reopened'} follow-up {f.title}", "followup", f.id, current_user.id); db.session.commit(); flash("Follow-up updated.", "success"); return redirect(request.referrer or url_for("records.followups"))

@bp.post("/followups/<int:record_id>/reschedule")
@login_required
def followup_reschedule(record_id):
    f=FollowUp.query.get_or_404(record_id)
    try: f.due_at=datetime.fromisoformat(request.form.get("due_at", "")); f.completed=False; db.session.commit(); flash("Follow-up rescheduled.", "success")
    except ValueError: flash("Enter a valid date and time.", "danger")
    return redirect(url_for("records.followups"))
