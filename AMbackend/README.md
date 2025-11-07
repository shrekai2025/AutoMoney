# AutoMoney Backend v2.0

AutoMoney AI Trading System Backend - Built with Python, FastAPI, and LangGraph

## Features

- **FastAPI** - Modern, fast web framework
- **LangGraph** - Multi-agent workflow orchestration
- **PostgreSQL + TimescaleDB** - Time-series data storage
- **Redis** - Caching and job scheduling
- **Google OAuth** - Secure authentication
- **Multi-LLM Support** - OpenRouter + Tuzi integration

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16+
- Redis 7+

### Installation

1. Clone the repository
```bash
cd AMbackend
```

2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
make dev
```

4. Configure environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Docker services
```bash
make docker-up
```

6. Run database migrations
```bash
make migrate
```

7. Start development server
```bash
make run
```

Visit http://localhost:8000/docs for API documentation.

## Project Structure

```
AMbackend/
├── app/
│   ├── api/            # API endpoints
│   ├── agents/         # LangGraph agents
│   ├── services/       # Business logic
│   ├── models/         # Database models
│   ├── db/             # Database configuration
│   ├── core/           # Core utilities
│   └── workflows/      # LangGraph workflows
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── scripts/            # Utility scripts
└── alembic/            # Database migrations
```

## Development

### Code Quality

Format code:
```bash
make format
```

Run linting:
```bash
make lint
```

Run tests:
```bash
make test
```

### Database Migrations

Create migration:
```bash
make migrate-create
```

Apply migrations:
```bash
make migrate
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

Proprietary - All rights reserved
