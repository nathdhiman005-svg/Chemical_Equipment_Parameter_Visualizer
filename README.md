# Secure Multi-User Chemical Equipment Parameter Visualizer

A full-stack application for uploading, visualizing, and reporting chemical equipment parameters — with strict per-user data isolation.

## Live Deployment

| Service | URL |
|---|---|
| **Frontend (Vercel)** | https://chemical-equipment-parameter-visual-sage.vercel.app |
| **Backend API (Render)** | https://chemical-equipment-parameter-visualizer-xq36.onrender.com/api/ |

## Architecture

| Layer | Technology |
|---|---|
| **Backend API** | Django 4.2 + Django REST Framework + SimpleJWT |
| **Web Frontend** | React 18 + Chart.js |
| **Desktop Frontend** | PyQt5 + Matplotlib |
| **Database (Local)** | SQLite |
| **Database (Production)** | PostgreSQL (Render) |
| **PDF Reports** | ReportLab |

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/nathdhiman005-svg/Chemical_Equipment_Parameter_Visualizer.git
cd Chemical_Equipment_Parameter_Visualizer
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations users equipment
python manage.py migrate

# Create an admin superuser
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`  
Django admin panel at `http://127.0.0.1:8000/admin/`

### 3. Web Frontend Setup

```bash
cd web_frontend

# Install dependencies
npm install

# Start the development server
npm start
```

Opens at `http://localhost:3000`

> The `.env.development` file is pre-configured to point at `http://127.0.0.1:8000/api`.  
> No additional configuration is needed for local development.

### 4. Desktop Frontend Setup

```bash
cd desktop_frontend

# Install dependencies (use the backend venv or create a separate one)
pip install -r requirements.txt

# Run the application
python main.py
```

> The desktop app connects to `http://127.0.0.1:8000/api` by default.  
> Make sure the backend server is running before launching.

---

## Environment Variables

### Backend (`backend/core/settings.py`)

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(insecure dev key)* | Django secret key — set a strong random value in production |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hosts |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | PostgreSQL connection string for production |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed frontend origins |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated trusted origins for CSRF |

### Frontend (`web_frontend/.env.development`)

| Variable | Default | Description |
|---|---|---|
| `REACT_APP_API_URL` | `http://127.0.0.1:8000/api` | Backend API base URL |

---

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