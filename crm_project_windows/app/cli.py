import os
import click
from datetime import datetime, timedelta
from decimal import Decimal
from app import db
from app.models import User, Customer, Lead, Opportunity, FollowUp, Activity

def seed_demo():
    """Create a repeatable fictional dataset. Does not reset existing data."""
    if User.query.filter_by(email="admin@example.com").first():
        print("Demo data already exists (admin@example.com).")
        return
    if os.getenv("VERCEL") and not os.getenv("DEMO_ADMIN_PASSWORD"):
        raise click.ClickException("Do not seed the public demo password on Vercel. Create a private admin with: flask --app index.py create-admin")
    admin=User(name="Avery Morgan",email="admin@example.com",role="admin"); admin.set_password(os.getenv("DEMO_ADMIN_PASSWORD", "ChangeMe123!")); db.session.add(admin)
    rep=User(name="Jordan Lee",email="jordan@example.com",role="employee"); rep.set_password("ChangeMe123!"); db.session.add(rep); db.session.flush()
    customers=[]
    for name,company,email,industry in [("Mira Shah","Northstar Labs","mira@northstar.example","Technology"),("Dev Mehta","Bluepeak Retail","dev@bluepeak.example","Retail"),("Anika Rao","Cedar Health","anika@cedar.example","Healthcare")]:
        c=Customer(name=name,company=company,email=email,industry=industry,customer_type="Customer",assigned_to=rep.id,notes="Fictional demonstration record"); db.session.add(c); customers.append(c)
    db.session.flush()
    for name,status,value,priority in [("Northstar CRM rollout","Qualified",Decimal("850000"),"High"),("Bluepeak analytics pilot","Negotiation",Decimal("420000"),"Medium"),("Cedar support renewal","Converted",Decimal("280000"),"Low"),("Atlas onboarding","New",Decimal("190000"),"Medium"),("Juniper platform upgrade","Lost",Decimal("125000"),"Low")]:
        l=Lead(name=name,company=name.split()[0],status=status,expected_value=value,priority=priority,assigned_to=rep.id,notes="Fictional demonstration record"); db.session.add(l); db.session.flush()
        if status in ("Qualified","Negotiation","Converted"):
            stage="Won" if status=="Converted" else ("Proposal" if status=="Negotiation" else "Qualification")
            db.session.add(Opportunity(name=name,company=l.company,stage=stage,expected_revenue=value,actual_revenue=value if stage=="Won" else 0,assigned_to=rep.id,lead_id=l.id,close_date=(datetime.utcnow()+timedelta(days=28)).date()))
    db.session.add(FollowUp(title="Discovery call with Mira",followup_type="Call",due_at=datetime.utcnow()+timedelta(days=1),customer_id=customers[0].id,assigned_to=rep.id,notes="Confirm team size and rollout needs."))
    db.session.add(FollowUp(title="Send renewal proposal",followup_type="Email",due_at=datetime.utcnow()-timedelta(days=1),customer_id=customers[2].id,assigned_to=rep.id,notes="Review support tiers."))
    db.session.add(Activity(message="Added customer Northstar Labs",entity_type="customer",user=admin)); db.session.commit()
    print("Created fictional demo records. Sign in: admin@example.com / ChangeMe123!")


def reset_password():
    """Set a local account password through hidden terminal prompts."""
    email = click.prompt("Account email").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException(f"No account exists for {email}. Run seed-demo first or check the email.")
    password = click.prompt("New password (minimum 8 characters)", hide_input=True, confirmation_prompt=True)
    if len(password) < 8:
        raise click.ClickException("Password must be at least 8 characters.")
    user.set_password(password)
    db.session.commit()
    click.echo(f"Password updated for {email}. Sign in with the new password.")


def create_admin():
    """Create an initial administrator using hidden password prompts."""
    name = click.prompt("Administrator name").strip()
    email = click.prompt("Administrator email").strip().lower()
    if not name or "@" not in email:
        raise click.ClickException("Enter a name and valid email address.")
    if User.query.filter_by(email=email).first():
        raise click.ClickException("An account with that email already exists.")
    password = click.prompt("Administrator password (minimum 12 characters)", hide_input=True, confirmation_prompt=True)
    if len(password) < 12:
        raise click.ClickException("Administrator password must be at least 12 characters.")
    user = User(name=name, email=email, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Administrator account created for {email}.")
