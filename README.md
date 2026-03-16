# College Canteen Management System (Django)

A full-stack Django application for managing college canteen operations, including user accounts, student ordering, kitchen workflow, staff management, and admin reporting.

## Features

- Custom User model and authentication
- Student food ordering and order status tracking
- Kitchen preparation & inventory handling
- Canteen staff operations and role-based access
- Admin dashboard with reports, order management
- Supabase (PostgreSQL) support via DATABASE_URL / SUPABASE_SQL

## Quick Start

1. Clone repository
   `ash
   git clone <repo-url>
   cd canteen
   `

2. Create venv and install
   `ash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   `

3. Create .env (example)
   `env
   SECRET_KEY= your-secret-key
   DEBUG=True
   SUPABASE_SQL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
   DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
   `

4. Migrate ;& run
   `ash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   `

5. Open http://127.0.0.1:8000

## Notes

- Use Supabase SQL (Postgres) or local SQLite for development depending on your .env settings.
- /templates contains frontend layout and pages.
- canteen_project/settings.py loads DB from SUPABASE_SQL or DATABASE_URL.

## GitHub repository description (short):

College Canteen Management System built with Django, featuring student orders, kitchen workflows, staff role management, and Supabase SQL compatibility.
