# Goal Tracker Backend

A production-grade FastAPI backend for the Goal & Habit Tracker application.

## Features

- **FastAPI** with async/await support
- **SQLAlchemy 2.x** with MySQL 8.x
- **JWT Authentication** with access and refresh tokens
- **Alembic** database migrations
- **Pydantic v2** for data validation
- **Docker** containerization
- **Comprehensive testing** with pytest
- **Code quality** tools (black, isort, ruff, mypy)

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your database credentials
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Run migrations**:
   ```bash
   docker-compose exec app alembic upgrade head
   ```

4. **Seed development data**:
   ```bash
   docker-compose exec app python -m app.utils.seed
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Local Development

1. **Install dependencies**:
   ```bash
   poetry install
   poetry shell
   ```

2. **Setup database**:
   ```bash
   # Start MySQL locally or use Docker
   docker run -d --name mysql-dev \
     -e MYSQL_ROOT_PASSWORD=rootpassword \
     -e MYSQL_DATABASE=goals \
     -e MYSQL_USER=goals \
     -e MYSQL_PASSWORD=goalspassword \
     -p 3306:3306 mysql:8.0
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local database URL
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Seed data**:
   ```bash
   python -m app.utils.seed
   ```

6. **Start development server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

### Authentication

Register a new user:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@local.test",
    "password": "Demo123!",
    "display_name": "Demo User"
  }'
```

Login:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@local.test",
    "password": "Demo123!"
  }'
```

### Goals

Create a goal:
```bash
curl -X POST "http://localhost:8000/api/v1/goals" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Read 20 Books",
    "description": "Read 20 books in 2025",
    "emoji": "📚",
    "goal_type": "count",
    "unit": "books",
    "target": 20,
    "timeframe_type": "fixed",
    "start_at": "2025-01-01T00:00:00Z",
    "end_at": "2025-12-31T23:59:59Z",
    "privacy": "private"
  }'
```

### Logs

Add a log entry:
```bash
curl -X POST "http://localhost:8000/api/v1/goals/{goal_id}/logs" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "value": 1,
    "note": "Finished reading 'Atomic Habits'",
    "date": "2025-01-15"
  }'
```

## Development

### Code Quality

Run linting and formatting:
```bash
pre-commit run --all-files
```

Or individually:
```bash
black app tests
isort app tests
ruff check app tests
mypy app
```

### Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: MySQL connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `JWT_EXPIRE_MIN`: Access token expiration (minutes)
- `JWT_REFRESH_EXPIRE_DAYS`: Refresh token expiration (days)
- `TZ`: Timezone (default: Asia/Bangkok)

## Project Structure

```
backend/
├── app/
│   ├── core/           # Settings, security, database
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── api/           # API routers
│   ├── services/      # Business logic
│   ├── repositories/  # Data access
│   ├── utils/         # Utilities
│   └── main.py        # FastAPI app
├── migrations/        # Alembic migrations
├── tests/            # Test suite
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Production Deployment

1. **Build production image**:
   ```bash
   docker build -t goal-tracker-backend .
   ```

2. **Deploy with production settings**:
   ```bash
   docker run -d \
     --name goal-tracker-backend \
     -p 8000:8000 \
     -e DATABASE_URL="mysql+pymysql://user:pass@host:3306/goals" \
     -e JWT_SECRET="your-production-secret" \
     goal-tracker-backend
   ```

## License

MIT License - see LICENSE file for details.

cd /Users/heva/Desktop/goal-project/backend && export PATH="$HOME/.local/bin:$PATH" && poetry install

cd /Users/heva/Desktop/goal-project/backend && export PATH="$HOME/.local/bin:$PATH" && poetry run python run.py