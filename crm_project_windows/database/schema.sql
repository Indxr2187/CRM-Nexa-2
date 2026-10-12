-- PostgreSQL reference schema (Neon or another PostgreSQL provider).
-- Select the target database first, then run this file with psql if desired.
-- The normal setup path is: python -m flask --app index.py init-db
CREATE TABLE IF NOT EXISTS app_user (
 id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
 email VARCHAR(160) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL,
 role VARCHAR(20) NOT NULL DEFAULT 'employee', active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_app_user_email ON app_user(email);

CREATE TABLE IF NOT EXISTS customer (
 id SERIAL PRIMARY KEY, name VARCHAR(120) NOT NULL, company VARCHAR(140),
 email VARCHAR(160), phone VARCHAR(40), address TEXT, industry VARCHAR(100),
 customer_type VARCHAR(40) DEFAULT 'Prospect', assigned_to INTEGER, notes TEXT,
 created_at TIMESTAMP NOT NULL,
 CONSTRAINT fk_customer_assignee FOREIGN KEY (assigned_to) REFERENCES app_user(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_customer_name ON customer(name);

CREATE TABLE IF NOT EXISTS sales_lead (
 id SERIAL PRIMARY KEY, name VARCHAR(120) NOT NULL, company VARCHAR(140),
 email VARCHAR(160), phone VARCHAR(40), source VARCHAR(80), status VARCHAR(30) NOT NULL DEFAULT 'New',
 priority VARCHAR(20) NOT NULL DEFAULT 'Medium', expected_value NUMERIC(12,2) NOT NULL DEFAULT 0,
 assigned_to INTEGER, customer_id INTEGER, notes TEXT, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
 CONSTRAINT fk_lead_assignee FOREIGN KEY (assigned_to) REFERENCES app_user(id) ON DELETE SET NULL,
 CONSTRAINT fk_lead_customer FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_sales_lead_name ON sales_lead(name);
CREATE INDEX IF NOT EXISTS ix_sales_lead_status ON sales_lead(status);

CREATE TABLE IF NOT EXISTS opportunity (
 id SERIAL PRIMARY KEY, name VARCHAR(140) NOT NULL, company VARCHAR(140),
 stage VARCHAR(30) NOT NULL DEFAULT 'Prospecting', expected_revenue NUMERIC(12,2) NOT NULL DEFAULT 0,
 actual_revenue NUMERIC(12,2) NOT NULL DEFAULT 0, close_date DATE, lead_id INTEGER, assigned_to INTEGER,
 notes TEXT, created_at TIMESTAMP NOT NULL,
 CONSTRAINT fk_opp_lead FOREIGN KEY (lead_id) REFERENCES sales_lead(id) ON DELETE SET NULL,
 CONSTRAINT fk_opp_assignee FOREIGN KEY (assigned_to) REFERENCES app_user(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_opportunity_stage ON opportunity(stage);

CREATE TABLE IF NOT EXISTS follow_up (
 id SERIAL PRIMARY KEY, title VARCHAR(140) NOT NULL, followup_type VARCHAR(20) NOT NULL DEFAULT 'Call',
 due_at TIMESTAMP NOT NULL, completed BOOLEAN NOT NULL DEFAULT FALSE, notes TEXT, customer_id INTEGER, lead_id INTEGER,
 assigned_to INTEGER, created_at TIMESTAMP NOT NULL,
 CONSTRAINT fk_followup_customer FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE,
 CONSTRAINT fk_followup_lead FOREIGN KEY (lead_id) REFERENCES sales_lead(id) ON DELETE CASCADE,
 CONSTRAINT fk_followup_assignee FOREIGN KEY (assigned_to) REFERENCES app_user(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_followup_due_at ON follow_up(due_at);

CREATE TABLE IF NOT EXISTS activity (
 id SERIAL PRIMARY KEY, message VARCHAR(255) NOT NULL, entity_type VARCHAR(40), entity_id INTEGER,
 user_id INTEGER, created_at TIMESTAMP NOT NULL,
 CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_activity_created_at ON activity(created_at);
