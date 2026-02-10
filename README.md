# Launch Inertia

Full-stack Django + Inertia.js + React application for managing contacts, billing, and notifications.

## Tech Stack

### Backend
- **Django 5.1+** - Web framework
- **Inertia.js** - Server-side rendering adapter
- **PostgreSQL** - Database
- **Redis** - Cache & Celery broker
- **Celery** - Background tasks
- **Django Channels** - WebSocket support
- **uv** - Fast Python package manager

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library

## Project Structure

```
launch-inertia/
├── src/                          # Django backend
│   ├── config/                   # Django configuration
│   │   └── settings/             # Split settings (base/dev/prod)
│   ├── core/                     # Core infrastructure
│   │   ├── shared/               # Base models, mixins, managers
│   │   └── inertia/              # Inertia.js helpers
│   ├── apps/                     # Business domains
│   │   ├── identity/             # Users, auth, profiles
│   │   ├── contacts/             # CRM
│   │   ├── billing/              # Stripe integration
│   │   └── notifications/        # Multi-channel notifications
│   └── infrastructure/           # Cache, email, tasks, monitoring
├── frontend/                     # React + Vite
│   └── src/
│       ├── pages/                # Inertia page components
│       ├── layouts/              # Layout components
│       └── components/           # Reusable components
├── templates/                    # Django templates
├── static/                       # Static files
└── media/                        # User uploads
```

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates .venv automatically)
uv sync

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Create database
createdb launch_inertia

# Run migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Run development server
uv run python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Running Both

Open two terminals:

```bash
# Terminal 1: Django
uv run python manage.py runserver

# Terminal 2: Vite
cd frontend && npm run dev
```

Visit http://localhost:8000

## Features

### Identity (Authentication)
- Email-based authentication
- Email verification
- Two-factor authentication (TOTP)
- Profile management
- Account security (lockout, password reset)

### Contacts (CRM)
- Contact management with custom fields
- Tags and categorization
- Lead scoring
- Multiple emails/phones per contact
- Notes and activity log
- Import/export

### Billing (Stripe)
- Subscription management
- Checkout sessions
- Customer portal
- Webhook handling

### Notifications
- Multi-channel (in-app, email, push)
- Real-time via WebSocket
- Templates with variables
- Read/unread tracking

## Development

### Package Management with uv

```bash
# Sync all dependencies
uv sync

# Sync with dev dependencies
uv sync --dev

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade
```

### Code Style

```bash
# Format code
uv run black src/
uv run ruff check src/ --fix

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

### Database Migrations

```bash
# Create migration
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate
```

### Celery Workers

```bash
# Start worker
uv run celery -A infrastructure.tasks worker -l INFO

# Start beat (scheduled tasks)
uv run celery -A infrastructure.tasks beat -l INFO
```

### Django Shell

```bash
# Interactive shell with IPython
uv run python manage.py shell_plus
```

## Production

### Environment Variables

Set `DJANGO_ENV=production` and configure:
- `SECRET_KEY` - Strong random key
- `ALLOWED_HOSTS` - Your domain
- `CSRF_TRUSTED_ORIGINS` - Your domain with https
- Database and Redis URLs
- Stripe live keys
- AWS credentials for SES and S3

### Build Frontend

```bash
cd frontend
npm run build
```

Static files will be output to `static/dist/`.

### Collect Static

```bash
uv run python manage.py collectstatic
```

### Production with uv

```bash
# Install only production dependencies
uv sync --no-dev

# Run with gunicorn
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## License

MIT
