# AggressiveSMS

A Flask web app for internal teams to monitor, manage, and follow up on flagged SMS conversations from clients.

## Features
- Login via SQL Server Users table (Flask-Login, bcrypt)
- Unified dashboard for flagged messages
- Keyword manager (add/edit/delete)
- Follow-up tracking
- Admin panel for SuperAdmin
- Email alerts (Flask-Mail)
- CSV/Excel reports
- Hourly/daily scheduled tasks (APScheduler)

## Setup
1. `python3 -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Set up `.env` with DB and mail config (see `.env` example)
4. Build Tailwind CSS: `npx tailwindcss -i ./app/static/tailwind.css -o ./app/static/tailwind.css --watch`
5. Run: `python run.py`

## Environment Variables (.env)
- SECRET_KEY
- DB_SERVER
- DB_NAME
- DB_USER
- DB_PASSWORD
- MAIL_SERVER
- MAIL_PORT
- MAIL_USERNAME
- MAIL_PASSWORD
- MAIL_USE_TLS
- MAIL_DEFAULT_SENDER

## Notes
- SuperAdmin: lindsey.stevens@tra
- Scaffold includes placeholders and dummy logic for rapid prototyping. 