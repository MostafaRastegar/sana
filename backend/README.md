# Djankit - Django REST Framework Project

A modern Django REST Framework project template with comprehensive configuration, best practices, and development guidelines.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Default Users and Test Credentials](#default-users-and-test-credentials)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Infrastructure
- **Modern Django Setup**: Django 5.2.9 with comprehensive configuration
- **REST API**: Django REST Framework 3.16.0 with Spectacular documentation
- **Authentication**: JWT-based authentication with refresh token rotation
- **Database**: PostgreSQL (production) and SQLite (development) support
- **Caching**: Redis-based caching and session storage
- **Background Tasks**: Celery integration with Redis broker

### Development Tools
- **Code Quality**: Black, isort, pylint, and mypy for consistent code quality
- **Testing**: pytest with coverage reporting
- **Containerization**: Docker and docker-compose for easy deployment
- **Environment Management**: django-environ for flexible configuration
- **Internationalization**: Persian and English language support

### Security & Performance
- **Security Headers**: Comprehensive security middleware and CORS configuration
- **Rate Limiting**: API rate limiting to prevent abuse
- **Error Handling**: Custom exception handler with structured responses
- **Performance**: Optimized configuration for production deployment

## Technology Stack

### Backend
- **Python**: 3.13.2
- **Django**: 5.2.9
- **Django REST Framework**: 3.16.0
- **Celery**: 5.5.2 (Background tasks)
- **Redis**: 5.2.1 (Caching and task broker)

### Database
- **PostgreSQL**: 16.1 (Production)
- **SQLite**: 3.45.3 (Development)

### Development Tools
- **Black**: 25.1.0 (Code formatting)
- **isort**: 5.13.2 (Import sorting)
- **pylint**: 3.4.0 (Code linting)
- **mypy**: 1.15.0 (Type checking)
- **pytest**: 8.4.1 (Testing framework)

### Containerization
- **Docker**: Multi-stage builds with uv package manager
- **docker-compose**: Development and production environments

## Prerequisites

### System Requirements
- Python 3.11 or higher
- PostgreSQL 16.1 or higher (for production)
- Redis 5.2 or higher
- Docker and docker-compose (optional, for containerized deployment)

### Development Environment
```bash
# Install Python dependencies
pip install uv
```

### Installation

### Option 1: Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd djankit
```

2. **Create virtual environment**
```bash
uv sync
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. **Run database migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Create test users**
```bash
python create_test_users.py
```

8. **Start development server**
```bash
python manage.py runserver
```

### Option 2: Docker Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd djankit
```

2. **Build and run containers**
```bash
docker-compose up --build
```

3. **Access the application**
- Django API: http://localhost:8000
- Admin panel: http://localhost:8000/admin

### Option 3: Production Deployment

1. **Build production image**
```bash
docker build -t djankit:production .
```

2. **Deploy with docker-compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration

### Environment Variables

The project uses environment variables for configuration. Copy `.env.example` to `.env` and customize the following:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL: postgresql://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379/1

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256

# File Storage
FILE_STORAGE=django.core.files.storage.FileSystemStorage
# For S3: minio_storage.storage.MinioMediaStorage

# MinIO/S3 (Optional)
MINIO_STORAGE_ENDPOINT=localhost:9000
MINIO_STORAGE_ACCESS_KEY=minioadmin
MINIO_STORAGE_SECRET_KEY=minioadmin
MINIO_STORAGE_BUCKET_NAME=djankit-files
```

### Settings Files

- **Development**: `config/settings/development.py`
- **Production**: `config/settings/production.py`
- **Base**: `config/settings/base.py`
- **Test**: `config/settings/test.py`

## Development

### Code Quality

The project enforces high code quality standards:

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint code with pylint
pylint example/ core/

# Type checking with mypy
mypy example/ core/

# Run all quality checks
make lint
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report --show-missing

# Run specific test
python manage.py test example.tests

# Run tests with pytest
pytest
```

### API Documentation

Access the auto-generated API documentation:

- **Development**: http://localhost:8000/api/docs/
- **Redoc**: http://localhost:8000/api/schema/redoc/

### Celery Tasks

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (scheduled tasks)
celery -A config beat -l info

# Monitor Celery with Flower
celery -A config flower
```

## Default Users and Test Credentials

The project includes a script to create test users with different permission levels for development and testing purposes.

### Test Users

Run the following command to create test users:

```bash
python create_test_users.py
```

This script creates the following users:

#### Admin User
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`
- **Permissions**: Full admin access, superuser privileges
- **Access**: Admin panel, all API endpoints

#### Staff User
- **Username**: `staff`
- **Password**: `staff123`
- **Email**: `staff@example.com`
- **Permissions**: Staff access, can access admin panel
- **Access**: Admin panel (limited), authenticated API endpoints

#### Regular User
- **Username**: `user`
- **Password**: `user123`
- **Email**: `user@example.com`
- **Permissions**: Standard user access
- **Access**: Authenticated API endpoints only

#### Test User
- **Username**: `testuser`
- **Password**: `test123`
- **Email**: `test@example.com`
- **Permissions**: Standard user access
- **Access**: Authenticated API endpoints only

### Authentication

To obtain JWT tokens for API access, use the following endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

The response will include:
- `access`: JWT access token (valid for 60 minutes)
- `refresh`: JWT refresh token (valid for 1 day)

### Admin Panel Access

Access the Django admin panel using the admin credentials:

- **URL**: http://127.0.0.1:8000/admin/
- **Username**: `admin`
- **Password**: `admin123`

### API Documentation Access

The API documentation is available at:

- **Development**: http://127.0.0.1:8000/api/docs/
- **Redoc**: http://127.0.0.1:8000/api/schema/redoc/

All documentation endpoints are publicly accessible for development purposes.

## Documentation

### Development Guidelines

Comprehensive development guidelines are available in the `docs/` directory:

- **[Development Guidelines](docs/Development_Guidelines.md)**: Complete development workflow and best practices
- **[CRUD Patterns Guide](docs/CRUD_Patterns_Guide.md)**: RESTful API development patterns
- **[Documentation Structure](docs/Documentation_Structure.md)**: How to organize project documentation

### Cline Rules

Project-specific development rules are defined in `.clinerules/`:

- **[Django REST Framework Best Practices](.clinerules/Django_REST_Framework_Best_Practices.md)**
- **[Security and Authentication](.clinerules/Security_and_Authentication.md)**
- **[Performance and Optimization](.clinerules/Performance_and_Optimization.md)**
- **[Testing and Code Quality](.clinerules/Testing_and_Code_Quality.md)**

### Memory Bank

The project maintains a comprehensive memory bank in `memory-bank/`:

- **[Project Brief](memory-bank/projectbrief.md)**: Project overview and goals
- **[Product Context](memory-bank/productContext.md)**: User experience and requirements
- **[System Patterns](memory-bank/systemPatterns.md)**: Architecture and design patterns
- **[Technical Context](memory-bank/techContext.md)**: Technology stack and configuration
- **[Active Context](memory-bank/activeContext.md)**: Current development state
- **[Progress](memory-bank/progress.md)**: Implementation status and roadmap

## Project Structure

```
djankit/
├── config/                 # Django project configuration
│   ├── settings/          # Environment-specific settings
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── core/                 # Core application with shared utilities
│   ├── __init__.py
│   ├── base_exception.py # Custom exception handling
│   ├── celery.py         # Celery configuration
│   ├── middleware.py     # Custom middleware
│   ├── permissions.py    # Permission classes
│   ├── serializers.py    # Base serializers
│   └── utils/           # Utility modules
├── example/             # Example application (replace with your apps)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── migrations/
├── docs/               # Project documentation
├── locale/             # Internationalization files
├── memory-bank/        # Project knowledge base
├── cline_rules/        # Development rules and guidelines
├── requirements.txt    # Production dependencies
├── requirements-dev.txt # Development dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Development containers
├── manage.py          # Django management script
└── README.md          # This file
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make changes** following the [development guidelines](docs/Development_Guidelines.md)
4. **Run tests**: `python manage.py test`
5. **Check code quality**: `make lint`
6. **Commit changes**: `git commit -m "Add your feature"`
7. **Push to branch**: `git push origin feature/your-feature`
8. **Create pull request**

### Code Review Process

- All changes must pass code quality checks
- Tests must be included for new features
- Documentation must be updated for API changes
- Pull requests require approval from maintainers

### Development Guidelines

Follow the comprehensive [development guidelines](docs/Development_Guidelines.md) for:
- Code style and formatting
- Testing practices
- API design patterns
- Security best practices
- Performance optimization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- All contributors and maintainers of the dependencies used
- The open-source community for providing excellent tools and libraries

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the [documentation](docs/)
- Review the [memory bank](memory-bank/) for project context

---

**Note**: This is a template project. Replace the `example` app with your actual Django applications and customize the configuration according to your needs.