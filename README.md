# Secure Multi-User Chemical Equipment Parameter Visualizer

A full-stack application for uploading, visualizing, and reporting chemical equipment parameters — with strict per-user data isolation.

## Architecture

| Layer | Technology |
|---|---|
| **Backend API** | Django 4.2 + Django REST Framework + SimpleJWT |
| **Web Frontend** | React 18 + Chart.js |
| **Desktop Frontend** | PyQt5 + Matplotlib |
| **Database** | SQLite (per-user data isolation via FK + queryset filtering) |
| **PDF Reports** | ReportLab |

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py makemigrations users equipment
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API available at `http://127.0.0.1:8000/api/`

### 2. Web Frontend

```bash
cd web_frontend
npm install
npm start
```

Opens at `http://localhost:3000`

### 3. Desktop Frontend

```bash
cd desktop_frontend
pip install -r requirements.txt
python main.py
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Register a new user |
| POST | `/api/auth/login/` | Public | Get JWT access + refresh tokens |
| POST | `/api/auth/token/refresh/` | Public | Refresh an expired access token |
| GET | `/api/auth/profile/` | JWT | Current user profile |
| POST | `/api/equipment/upload/` | JWT | Upload a CSV file |
| GET | `/api/equipment/stats/` | JWT | Aggregated equipment statistics |
| GET | `/api/equipment/history/` | JWT | Last 5 upload records |
| GET | `/api/equipment/data/` | JWT | All equipment data for the user |
| GET | `/api/equipment/report/` | JWT | Download a PDF report |

## CSV Format

```
equipment_name,parameter_name,value,unit
Reactor A,Temperature,350.5,°C
```

Required columns: `equipment_name`, `parameter_name`, `value`
Optional column: `unit`

## Security

- **JWT Authentication** with 30-minute access tokens and 1-day refresh tokens.
- **Per-user data isolation**: Every queryset is filtered by `request.user`.
- **Admin panel** at `/admin/` shows all data with cascading deletes.
- **401 interceptors** in both frontends prompt for re-login on expiry.