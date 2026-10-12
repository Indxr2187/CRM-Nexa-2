# Nexa CRM — Windows 11 Project

A complete Flask CRM for customers, leads, sales opportunities, follow-ups, employee accounts, activity, and reports. This copy is prepared for **Windows 11 + PowerShell + VS Code** and deployment to **Vercel**.

## Technology choices

- Python 3.12, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF.
- SQLite for local Windows development. No MySQL installation or setup is used.
- Neon PostgreSQL for persistent production data on Vercel.
- Vercel Python Functions host the Flask application. CSS and JavaScript are served from `public/static`.
- Bootstrap 5 and Chart.js are loaded by the browser from CDN links.

Vercel is the deployment/hosting service rather than an online compiler. After deployment, Vercel provides a `*.vercel.app` address. You can attach a separately owned custom domain in Vercel project settings.

## Part 1 — Run it on Windows 11

### 1. Extract and open the project

Extract `crm_project_windows.zip`. In VS Code choose **File → Open Folder** and open the extracted `crm_project_windows` folder. Open **Terminal → New Terminal** and check that the current directory contains `run.py`:

```powershell
Get-Location
Get-ChildItem
```

If `run.py` is not listed, change to the extracted project folder with `cd`, for example:

```powershell
cd "$HOME\Downloads\crm_project_windows"
```

### 2. Install Python 3.12

Check the Python launcher:

```powershell
py -3.12 --version
```

If Python 3.12 is not found, install it from [python.org/downloads/windows](https://www.python.org/downloads/windows/). During installation enable **Add Python to PATH**, then close and reopen VS Code and check the version again.

### 3. Create the virtual environment and install packages

Run these commands from the folder containing `run.py`:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The execution-policy setting applies only to the current PowerShell terminal. When `(.venv)` appears at the start of the prompt, the environment is active. After opening a new terminal, activate it again with:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Configure SQLite for local development

Create a local `.env` file and generate a private key:

```powershell
Copy-Item .env.example .env
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Open `.env` in VS Code. Keep `DATABASE_URL=sqlite:///crm.db` for local use and replace the example `SECRET_KEY` with the generated value. Do not share or commit `.env`.

### 5. Create tables and fictional local demo data

```powershell
python -m flask --app run.py init-db
python -m flask --app run.py seed-demo
```

The local-only seed creates fictional demo accounts:

- Admin: `admin@example.com`
- Employee: `jordan@example.com`
- Initial password for both: `ChangeMe123!`

These predictable demo credentials are for local evaluation only. Do not seed a public Vercel deployment with them. To make a private local admin instead, run `python -m flask --app run.py create-admin` and follow the prompts.

### 6. Start the app

```powershell
python -m flask --app run.py run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Stop the development server by pressing **Ctrl+C** in the terminal. If port 5000 is already occupied, use:

```powershell
python -m flask --app run.py run --debug --port 5001
```

Then open [http://127.0.0.1:5001](http://127.0.0.1:5001).

### 7. Reset a local password

From the activated environment, run:

```powershell
python -m flask --app run.py reset-password
```

Enter the account email, then type a new password at the hidden prompt.

## Part 2 — Deploy on Vercel

Vercel supports Flask applications through its Python runtime. This project exposes a top-level WSGI app in `index.py`, uses `public/static` for deployable assets, and sets Python 3.12. See [Vercel’s Flask deployment guide](https://vercel.com/docs/frameworks/backend/flask) and [Vercel Marketplace storage guide](https://vercel.com/docs/marketplace-storage).

### 1. Create a GitHub repository

Install [Git for Windows](https://git-scm.com/download/win) if needed. From the project directory, open PowerShell and run:

```powershell
git init
git add .
git commit -m "Windows CRM project for Vercel"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/nexa-crm-windows.git
git push -u origin main
```

Replace the remote URL with your own empty GitHub repository. If Git says a remote already exists, inspect it using `git remote -v`; do not add another remote. `.env`, `.venv`, SQLite databases, and temporary files are excluded by the ignore files.

### 2. Import the repository into Vercel

1. Sign in at [vercel.com](https://vercel.com/).
2. Choose **Add New → Project**, then import the GitHub repository.
3. Set **Root Directory** to `./` because the repository root should be the contents of `crm_project_windows`.
4. Keep the detected Python/Flask build settings. Do not set a Node.js build command or output directory.

### 3. Connect Neon PostgreSQL

In the Vercel project, open **Storage / Marketplace** and add a **Neon Postgres** integration. Connect it to the project and confirm Vercel provides a `DATABASE_URL` variable for the environments you plan to use.

In **Project Settings → Environment Variables**, add a `SECRET_KEY` value generated on your Windows machine:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep this value private. Set it for Production and for Preview/Development if you will use those environments. Vercel must have both `DATABASE_URL` and `SECRET_KEY` before it can run this project.

**Do not use `sqlite:///crm.db` on Vercel.** Serverless local files are not persistent. This project deliberately refuses to start on Vercel if it detects SQLite or the default development secret.

### 4. Deploy and initialize the hosted database

Deploy from the Vercel dashboard. Vercel creates a deployment URL ending in `.vercel.app`. After connecting Neon and setting the variables, trigger a redeployment if the first deployment was built before those variables existed.

For the initial database setup, install Node.js LTS and the Vercel CLI if you have not already:

```powershell
npm install --global vercel
vercel login
vercel link
```

In the linked project folder, initialize the **Production** Neon database and create your own administrator. These commands use the linked Vercel environment; the administrator password is entered privately in the terminal:

```powershell
vercel env run -e production -- python -m flask --app index.py init-db
vercel env run -e production -- python -m flask --app index.py create-admin
```

Use a unique password of at least 12 characters. Do not run `seed-demo` against the public deployment because it uses the well-known demonstration password. The `database/schema.sql` file is also provided as a PostgreSQL reference, but `init-db` is the normal setup command.

To attach a domain you own, open **Project → Settings → Domains** in Vercel and follow its DNS instructions. A domain purchase is separate from deployment.

## Tests

The automated suite uses a temporary SQLite database and will not change the configured Neon or local database:

```powershell
python -m unittest discover -s tests -v
```

For a local SQLite smoke check, first run `init-db` and `seed-demo`, then:

```powershell
python tests\smoke_check.py
```

## Troubleshooting

- **`py -3.12` not found:** install Python 3.12, enable **Add Python to PATH**, and restart VS Code.
- **Activation script blocked:** run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate `.venv` again.
- **`No module named flask`:** activate `.venv` and rerun `python -m pip install -r requirements.txt`.
- **Vercel reports missing `DATABASE_URL`:** reconnect Neon and enable its variable for the environment being deployed.
- **Vercel rejects SQLite:** use the Neon PostgreSQL connection string in Vercel; SQLite is local-only.
- **Login page says credentials are wrong:** local seeded credentials are `admin@example.com` / `ChangeMe123!`; for Vercel create the administrator with `create-admin` using the Production command above.
- **Vercel page shows a 500 error:** open the deployment’s **Functions/Runtime Logs** and check that `DATABASE_URL` and `SECRET_KEY` exist for that environment.
- **Port 5000 is busy:** use the `--port 5001` command shown above.

## Project files

```text
app/                 Flask application, models, routes, templates, local assets
public/static/       CSS and JavaScript served by Vercel
database/            PostgreSQL schema and seed notes
tests/               Automated tests and route smoke check
config.py            Environment-based database and session configuration
index.py             Vercel Flask entry point
run.py               Local Windows Flask entry point
requirements.txt     Python dependencies, including PostgreSQL driver
vercel.json          Vercel function configuration
.env.example         Local configuration template (no real secrets)
```
