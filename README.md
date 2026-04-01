# FastAPI Boilerplate

A production-ready FastAPI boilerplate with async everything, Django-like app structure, and a clean CLI.

## Tech Stack

- **FastAPI** — async web framework
- **Python 3.11+** — enforced via `.python-version`
- **UV** — fast package manager (10-100x faster than pip)
- **SQLAlchemy 2.0** — async ORM with `asyncpg`
- **Alembic** — async migrations
- **PostgreSQL** — database
- **Redis** — rate limiting cache
- **Typer** — CLI (Django management command style)

---

## Quick Start

```bash
# 1. Start postgres & redis
docker compose up -d

# 2. Install dependencies
uv sync

# 3. Run migrations
uv run python main.py migrate

# 4. Start server
uv run python main.py run --debug
```

App runs at `http://localhost:8080`. Docs at `http://localhost:8080/docs`.

---

## Project Structure

```
fastapi-boilerplate/
├── main.py                     # CLI entry point (like Django's manage.py)
├── pyproject.toml              # Dependencies & config
├── docker-compose.yml          # Postgres + Redis
├── .python-version             # Python 3.11
│
└── src/
    ├── server.py               # FastAPI app factory (create_app)
    ├── config.py               # Settings from .env
    ├── lifespan.py              # Startup/shutdown events
    ├── exceptions.py            # Global exception hierarchy
    ├── handlers.py              # Exception handlers
    ├── cli.py                   # All CLI commands
    │
    ├── apps/                    # Feature modules (like Django apps)
    │   ├── user/
    │   │   ├── models.py        # SQLAlchemy model
    │   │   ├── repository.py    # Data access layer
    │   │   ├── service.py       # Business logic
    │   │   ├── request.py       # Pydantic request schemas
    │   │   ├── response.py       # Pydantic response schemas
    │   │   ├── exceptions.py     # App-specific exceptions
    │   │   ├── urls.py          # Route handlers
    │   │   └── __init__.py      # Exports router
    │   │
    │   ├── master/              # Same 8-file pattern
    │   └── blog/                # Same 8-file pattern
    │
    ├── auth/                    # JWT, passwords, permissions
    │   ├── jwt.py               # JWToken class, create_tokens
    │   ├── permissions.py       # HasPermission, AdminHasPermission
    │   ├── password.py          # hash_password, verify_password
    │   └── role_types.py        # RoleType enum (USER, ADMIN, STAFF)
    │
    ├── db/                      # Database layer
    │   ├── session.py           # Async engine, db_session (commits on success)
    │   ├── base.py              # Base, TimeStampMixin, UUIDPrimaryKeyMixin
    │   └── redis.py             # Redis client
    │
    ├── utils/                   # Shared utilities
    │   ├── schema.py            # CamelCaseModel, BaseResponse
    │   ├── validation.py         # validate_email, strong_password
    │   ├── cookies.py            # set_auth_cookies, delete_cookies
    │   ├── scheduler.py          # APScheduler (background jobs)
    │   ├── http_client.py       # HTTPClient (httpx wrapper)
    │   └── webhook.py            # Webhook helpers
    │
    ├── constants/               # Constants (messages, regex, config)
    └── migrations/             # Alembic migrations
```

---

## CLI Commands

```bash
uv run python main.py --help

startapp        Create a new FastAPI app structure
startapps       Create multiple apps at once
makemigrations  Detect model changes & generate migration files
showmigrations Show all migrations with applied/unapplied status
migrate        Apply pending migrations
rollback       Rollback the last migration
run            Start the development server
```

**Examples:**
```bash
uv run python main.py startapp blog        # creates src/apps/blog/
uv run python main.py makemigrations        # generate migrations
uv run python main.py migrate              # apply migrations
uv run python main.py showmigrations      # check status
uv run python main.py rollback             # undo last migration
uv run python main.py run --debug         # dev server with hot reload
uv run python main.py run --port 3000     # custom port
```

---

## Creating a New App

```bash
# 1. Generate the app structure
uv run python main.py startapp blog

# 2. Register the router in src/apps/__init__.py
from apps.blog import blog_router
__all__ = ["user_router", "master_router", "blog_router"]

# 3. Add routes to the app in src/server.py
base_router.include_router(blog_router)

# 4. Create & apply migrations
uv run python main.py makemigrations
uv run python main.py migrate
```

---

## App Structure (8-File Pattern)

Each app follows the Django-like flat structure:

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy model with mixins |
| `repository.py` | Data access — all DB queries |
| `service.py` | Business logic — orchestrates repository |
| `request.py` | Pydantic schemas for incoming requests |
| `response.py` | Pydantic schemas for responses |
| `exceptions.py` | Custom exceptions specific to this app |
| `urls.py` | Route handlers (views) + router |
| `__init__.py` | Exports the router |

---

## Import Patterns

Like Django — **relative imports within the same app**, **absolute for cross-app and shared modules**:

```python
# Within the same app (like Django's from .models import)
from .models import UserModel
from .service import UserService
from .repository import UserRepository

# From another app (like Django's from blog.models import)
from apps.user.models import UserModel

# Shared modules (always absolute)
from auth.jwt import create_tokens
from db.session import db_session
from utils.schema import BaseResponse
```

---

## Async Everything

The entire stack is async:

- **Database**: `asyncpg` + SQLAlchemy async — `async_sessionmaker`, `AsyncSession`, `await session.scalar()`
- **Repository**: All methods are `async def` with `await`
- **Service**: All methods are `async def` with `await`
- **Routes**: All handlers are `async def`
- **CLI**: All commands are sync (CLI doesn't need async)

---

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
ENV=Local
APP_NAME=FastAPI-Starter-Pack
APP_VERSION=0.0.1
APP_HOST=0.0.0.0
APP_PORT=8080
APP_DEBUG=true

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXP=3600
REFRESH_TOKEN_EXP=86400
COOKIES_DOMAIN=localhost

DATABASE_USER=testuser
DATABASE_PASSWORD=testpass
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testdb
DATABASE_URL=postgresql+asyncpg://testuser:testpass@localhost:5432/testdb

REDIS_URL=redis://localhost:6379/0

MASTER_ENUM_FILE_PATH=/tmp/enums.json
SENTRY_SDK_DSN=https://example@sentry.io/123
```

---

## API Routes

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | Root health check | No |
| GET | `/healthcheck` | Health check | No |
| GET | `/master/enums` | Get all enums | No |
| POST | `/api/user/sign-in` | User login | No |
| POST | `/api/user` | Create user | No |
| GET | `/api/user/self` | Get current user | USER |
| GET | `/api/user/` | Get user by ID | USER |
| DELETE | `/api/user/` | Delete user | USER |

---

## Docker Services

```bash
# Start postgres and redis
docker compose up -d

# Check status
docker compose ps

# Stop services
docker compose down

# Stop and remove volumes (wipe data)
docker compose down -v
```

---

## Database Migrations

```bash
# Check for changes and generate migration
uv run python main.py makemigrations

# Apply all pending migrations
uv run python main.py migrate

# Show migration status
uv run python main.py showmigrations

# Rollback last migration
uv run python main.py rollback
```

---

## Requirements

- Python 3.11+
- UV (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (for postgres and redis)
