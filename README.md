# FastAPI Supabase Boilerplate

A production-ready FastAPI boilerplate with Supabase integration, JWT authentication, and clean architecture.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 🔐 **Supabase Integration** - Database and authentication
- 🛡️ **JWT Authentication** - Secure token-based authentication
- 🌐 **CORS Support** - Cross-origin resource sharing
- 📝 **Pydantic Models** - Data validation and serialization
- 🧪 **Testing** - Basic test structure with pytest
- 📊 **Logging** - Structured logging with configurable levels
- ⚙️ **Configuration** - Environment-based configuration
- 🔧 **Error Handling** - Global exception handling
- 📚 **API Documentation** - Auto-generated OpenAPI docs

## Project Structure

```
📁 project-root/
├── 📁 api/                    # API route handlers
│   ├── __init__.py
│   └── auth.py               # Authentication routes
├── 📁 core/                  # Core configuration and utilities
│   ├── __init__.py
│   ├── config.py             # Application settings
│   ├── database.py           # Database configuration
│   ├── dependencies.py       # Dependency injection
│   └── exceptions.py         # Custom exceptions
├── 📁 middlewares/           # Custom middlewares
│   ├── __init__.py
│   ├── jwt_middleware.py     # JWT authentication middleware
│   └── logger.py             # Request logging middleware
├── 📁 schemas/               # Pydantic models
│   ├── __init__.py
│   └── auth.py               # Authentication schemas
├── 📁 tests/                 # Test files
│   ├── __init__.py
│   └── test_auth.py          # Authentication tests
├── 📁 utils/                 # Utility functions
│   ├── __init__.py
│   └── supabase.py           # Supabase client utilities
├── 📁 venv/                  # Virtual environment (not in git)
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd wishlist-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

Required environment variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
APP_NAME=FastAPI Supabase Boilerplate
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 3. Run the Application

```bash
# Development mode
fastapi dev main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | User login | No |
| POST | `/auth/register` | User registration | No |
| POST | `/auth/logout` | User logout | No |
| GET | `/auth/me` | Get current user | Yes |
| POST | `/auth/forgot-password` | Send password reset | No |
| POST | `/auth/reset-password` | Reset password | No |


### System

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check | No |
| GET | `/` | Root endpoint | No |

## Adding New Routes

### 1. Create Route File

Create a new file in the `api/` directory:

```python
# api/items.py
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user

router = APIRouter()

@router.get("/items")
async def get_items(current_user=Depends(get_current_user)):
    return {"items": []}
```

### 2. Register Router

Add the router to `main.py`:

```python
from api import items

# Include API routers
app.include_router(items.router, prefix="/items", tags=["Items"])
```

### 3. Add Schemas (Optional)

Create Pydantic models in `schemas/`:

```python
# schemas/items.py
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
```

## Adding Middleware

### 1. Create Middleware

```python
# middlewares/custom_middleware.py
from fastapi import Request
import time

class CustomMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            start_time = time.time()
            
            # Your middleware logic here
            
        await self.app(scope, receive, send)
```

### 2. Register Middleware

Add to `main.py`:

```python
from middlewares.custom_middleware import CustomMiddleware

app.add_middleware(CustomMiddleware)
```

## Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## Development Tools

### Code Formatting

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Check code style with flake8
flake8 .
```

### Database Operations

If using direct PostgreSQL connection:

```python
from core.database import get_db

# Use in your routes
async def some_route(db=Depends(get_db)):
    # Database operations here
    pass
```

## Deployment

### Environment Variables

Set the following environment variables in production:

```env
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Security**: Use strong JWT secrets and enable HTTPS
2. **Database**: Use connection pooling for production
3. **Logging**: Configure structured logging for production
4. **Monitoring**: Add health checks and monitoring
5. **Rate Limiting**: Consider adding rate limiting middleware
6. **CORS**: Configure CORS origins for production domains

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions and support, please open an issue in the repository.
