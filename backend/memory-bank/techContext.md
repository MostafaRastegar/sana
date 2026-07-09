# Technical Context

## Technologies Used

### Core Framework
- **Django 5.2.9**: Web framework providing the foundation for the application
- **Django REST Framework 3.16.0**: REST API framework for building web APIs
- **Python 3.11+**: Programming language with modern features and performance

### Database & Storage
- **PostgreSQL**: Primary database for production environments
- **SQLite**: Development database for local development
- **Redis 6.1.0**: Caching, session storage, and Celery broker
- **MinIO/S3**: Object storage for file uploads and media files

### Authentication & Security
- **djangorestframework-simplejwt 5.5.0**: JWT authentication with refresh token support
- **django-cors-headers 4.7.0**: Cross-Origin Resource Sharing configuration
- **django-environ 0.12.0**: Environment-based configuration management

### Background Processing
- **Celery 5.5.2**: Distributed task queue for background processing
- **django-celery-beat 2.8.1**: Periodic task scheduling
- **django-celery-results 2.6.0**: Task result storage

### API Documentation
- **drf-spectacular 0.27.2**: OpenAPI 3.0 schema generation
- **drf-spectacular-sidecar**: Bundled frontend for API documentation

### File Handling & Utilities
- **Pillow 11.0.0**: Image processing and manipulation
- **django-storages 1.14.6**: Storage backends for cloud storage
- **boto3 1.38.23**: AWS SDK for Python (S3 integration)
- **openpyxl 3.1.5**: Excel file handling
- **pandas 2.2.3**: Data analysis and manipulation
- **xlsxwriter 3.2.9**: Excel file writing

### Development & Testing
- **pytest 7.4.3**: Testing framework
- **pytest-django 4.8.0**: Django integration for pytest
- **pytest-cov 4.1.0**: Coverage reporting
- **black 24.1.1**: Code formatting
- **isort 5.13.2**: Import sorting
- **pylint 3.0.3**: Code linting
- **mypy 1.7.1**: Static type checking

### Monitoring & Observability
- **elastic-apm 6.18.0**: Application Performance Monitoring
- **gevent 25.9.1**: Coroutine-based networking library

### Deployment & Infrastructure
- **gunicorn 23.0.0**: WSGI HTTP server
- **whitenoise 6.11.0**: Static file serving
- **Docker**: Containerization platform
- **docker-compose**: Multi-container application orchestration

## Current State (Updated: February 17, 2026)

### Project Technology Status
- **Framework**: Django 5.2.9 with Django REST Framework 3.16.0
- **Database**: SQLite (development), PostgreSQL support configured
- **Authentication**: JWT-based with djangorestframework-simplejwt
- **Background Tasks**: Celery with Redis broker configured
- **File Storage**: MinIO/S3 integration via django-storages
- **API Documentation**: DRF Spectacular with offline sidecar distribution
- **Internationalization**: Persian (fa) and English (en) support
- **Monitoring**: Elastic APM integration (configurable)

### Recent Technology Updates
- **Middleware**: Updated to use direct class inheritance instead of MiddlewareMixin
- **Type Safety**: Enhanced type checking in permissions module
- **Project Structure**: Streamlined by removing unused Django apps
- **Configuration**: Updated settings to reflect current project state

## Development Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL (for production-like development)
- Redis (for caching and Celery)
- Docker and docker-compose (for containerized development)

### Installation Steps

1. **Clone and Setup Virtual Environment**
```bash
git clone <repository-url>
cd team-backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install Dependencies**
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Install test dependencies
pip install -e ".[test]"
```

3. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: SECRET_KEY, DATABASE_URL, REDIS_URL
# Optional: MINIO settings, APM settings, etc.
```

4. **Database Setup**
```bash
# For PostgreSQL
createdb team_backend

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

5. **Static Files**
```bash
# Collect static files
python manage.py collectstatic
```

6. **Start Development Services**
```bash
# Start Redis (if not using docker-compose)
redis-server

# Start Celery worker
celery -A core worker -l info

# Start Celery beat (for scheduled tasks)
celery -A core beat -l info

# Start development server
python manage.py runserver
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Project Structure

### Current Django Apps Organization

```
team-backend/
├── config/                 # Django project configuration
│   ├── __init__.py
│   ├── asgi.py            # ASGI application entry point
│   ├── urls.py            # URL routing configuration
│   ├── wsgi.py            # WSGI application entry point
│   └── settings/          # Environment-specific settings
│       ├── __init__.py
│       ├── base.py        # Base settings shared across environments
│       ├── development.py # Development environment settings
│       ├── production.py  # Production environment settings
│       └── test.py        # Test environment settings
├── core/                  # Shared utilities and base classes
│   ├── __init__.py
│   ├── base_exception.py  # Custom exception handling
│   ├── celery.py          # Celery configuration
│   ├── context_processors.py # Django context processors
│   ├── middleware.py      # Custom middleware (updated)
│   ├── pagination.py      # Custom pagination classes
│   ├── permissions.py     # Custom permission classes (type-safe)
│   ├── schema.py          # API schema customization
│   ├── serializers.py     # Base serializers
│   ├── storages.py        # Custom storage backends
│   ├── validators.py      # Custom validators
│   └── views.py           # Base view classes
├── locale/                # Internationalization files
├── manage.py              # Django management script
├── requirements.txt       # Production dependencies
├── pyproject.toml         # Project configuration (Poetry/Build system)
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker services orchestration
└── gunicorn.conf.py       # Gunicorn WSGI server configuration
```

### Recent Structure Changes
- **Removed Apps**: Unused Django apps have been removed to streamline the project
- **Core Module**: Enhanced with updated middleware and type-safe permissions
- **Configuration**: Updated to reflect current project state and dependencies

## Configuration Management

### Environment Variables

The application uses environment-based configuration managed through `django-environ`:

**Required Variables:**
- `SECRET_KEY`: Django secret key for security
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string for caching and Celery

**Optional Variables:**
- `DEBUG`: Enable/disable debug mode
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `MINIO_*`: MinIO/S3 configuration for file storage
- `CELERY_*`: Celery configuration for background tasks
- `APM_*`: Elastic APM configuration for monitoring
- `JWT_*`: JWT token configuration

### Settings Organization

Settings are organized hierarchically:

1. **Base Settings** (`config/settings/base.py`): Common settings shared across all environments
2. **Environment Settings**: Environment-specific overrides
   - Development: `config/settings/development.py`
   - Production: `config/settings/production.py`
   - Test: `config/settings/test.py`

### Database Configuration

The application supports multiple database backends:

**PostgreSQL (Recommended for Production):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'team_backend',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**SQLite (Development):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## Development Workflow

### Code Quality Standards

1. **Code Formatting**: Use `black` for consistent code formatting
2. **Import Sorting**: Use `isort` for organized imports
3. **Linting**: Use `pylint` for code quality checks
4. **Type Checking**: Use `mypy` for static type analysis
5. **Testing**: Use `pytest` with coverage reporting

### Git Workflow

Recommended workflow:
1. Create feature branches from `main`
2. Use descriptive commit messages
3. Run tests and linting before pushing
4. Use pull requests for code review
5. Squash commits before merging

### Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test REST endpoints with pytest
4. **Coverage**: Maintain >80% code coverage

### Continuous Integration

The project should include CI/CD pipeline with:
- Automated testing on pull requests
- Code quality checks (linting, formatting)
- Security vulnerability scanning
- Automated deployment to staging/production

## Performance Considerations

### Database Optimization
- Use `select_related()` and `prefetch_related()` for query optimization
- Implement proper database indexing
- Use connection pooling in production
- Consider read replicas for high-traffic scenarios

### Caching Strategy
- Redis for session storage and caching
- Cache frequently accessed data
- Implement cache invalidation strategies
- Use cache warming for critical data

### Static Files
- Use Whitenoise for static file serving
- Implement CDN for production static files
- Enable compression for static assets

### Background Processing
- Use Celery for long-running tasks
- Implement proper task retry logic
- Monitor task queue performance
- Use dedicated queues for different task types

## Security Considerations

### Authentication & Authorization
- JWT tokens with proper expiration
- Token blacklisting on logout
- Refresh token rotation
- Role-based permissions

### Input Validation
- Comprehensive serializer validation
- Custom validators for business rules
- XSS and CSRF protection
- SQL injection prevention

### Data Protection
- HTTPS enforcement in production
- Secure cookie configuration
- Sensitive data encryption
- Proper error message handling

## Recent Technology Improvements

### 1. Middleware Updates
- **Change**: Replaced MiddlewareMixin with direct class inheritance
- **Benefit**: Better Django compatibility and cleaner code
- **Impact**: Improved maintainability and reduced dependencies

### 2. Type Safety Enhancements
- **Change**: Fixed type checking issues in permissions module
- **Benefit**: Better IDE support and fewer runtime errors
- **Impact**: Improved development experience and code reliability

### 3. Project Structure Streamlining
- **Change**: Removed unused Django apps
- **Benefit**: Cleaner project structure and faster development
- **Impact**: Reduced complexity and improved maintainability

This technical context provides the foundation for understanding the project's architecture, dependencies, and development practices.
