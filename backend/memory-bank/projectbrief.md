# Project Brief

## Project Overview

**Team Backend** is a production-ready Django REST Framework application designed for team management systems. It provides a comprehensive API for managing users, teams, and related functionality with enterprise-grade features.

## Current State (Updated: February 17, 2026)

### Project Structure
- **Core Framework**: Django 5.2.9 with Django REST Framework 3.16.0
- **Database**: SQLite (development), PostgreSQL support configured
- **Authentication**: JWT-based with djangorestframework-simplejwt
- **API Documentation**: DRF Spectacular with offline sidecar distribution
- **Background Tasks**: Celery with Redis broker
- **Internationalization**: Persian (fa) and English (en) support
- **File Storage**: MinIO/S3 integration via django-storages
- **Monitoring**: Elastic APM integration (configurable)

### Core Components Implemented
- **Core Module**: Shared utilities, middleware, permissions, serializers
- **Exception Handling**: Custom exception handler with structured responses
- **Middleware**: HTTP method restriction and API language detection
- **Permissions**: Model-based permission system for ViewSets
- **Celery**: Task queue configuration with beat scheduling
- **Settings**: Multi-environment configuration (development, production, test)

### Recent Changes
- **App Cleanup**: Removed unused Django apps to streamline project structure
- **Middleware Updates**: Replaced MiddlewareMixin with direct class inheritance for Django compatibility
- **Type Safety**: Fixed type checking issues in permissions module
- **Configuration**: Updated settings to reflect current project state

## Core Requirements

### Essential Features
- **User Management**: Complete user registration, authentication, and profile management
- **Team Management**: Create, manage, and organize teams with hierarchical structures
- **API Documentation**: Auto-generated, interactive API documentation using DRF Spectacular
- **Authentication**: JWT-based authentication with refresh token rotation
- **Internationalization**: Support for Persian (fa) and English (en) languages
- **File Storage**: Object storage integration (MinIO/S3) for media files
- **Background Tasks**: Celery integration for asynchronous task processing
- **Monitoring**: Elastic APM integration for performance monitoring

### Technical Requirements
- **Database**: PostgreSQL primary database with SQLite fallback for development
- **Caching**: Redis-based caching and session storage
- **Security**: Comprehensive security middleware, CORS configuration, and input validation
- **Performance**: Optimized for production deployment with connection pooling
- **Scalability**: Container-ready with Docker and docker-compose support
- **Testing**: pytest-based testing framework with coverage reporting

### Infrastructure Requirements
- **Containerization**: Docker support with multi-stage builds
- **Orchestration**: docker-compose for local development and testing
- **Static Files**: Whitenoise for static file serving in production
- **Logging**: Structured logging with multiple handlers
- **Environment**: Environment-based configuration management

## Project Scope

### In Scope
- Complete REST API for team and user management
- JWT authentication with token blacklisting
- File upload and management via object storage
- Background task processing with Celery
- API documentation generation
- Internationalization support
- Production-ready deployment configuration
- Comprehensive error handling and validation

### Out of Scope
- Frontend application (this is backend-only)
- Real-time communication features (WebSockets)
- Advanced analytics or reporting
- Third-party integrations beyond storage and monitoring
- Mobile app development

## Success Criteria

1. **API Completeness**: All core team management features accessible via REST API
2. **Performance**: Handle concurrent requests efficiently with proper caching
3. **Security**: No security vulnerabilities in authentication or data handling
4. **Documentation**: Complete API documentation with examples
5. **Deployability**: One-command deployment to production environment
6. **Maintainability**: Clean, well-structured code following Django best practices
7. **Monitoring**: Full observability with APM and structured logging

## Constraints

- **Python Version**: Must support Python 3.11+
- **Django Version**: Django 5.2.9
- **Database**: PostgreSQL for production, SQLite for development
- **License**: Open source with appropriate licensing
- **Dependencies**: All dependencies must be production-ready and actively maintained

## Assumptions

- Users have basic knowledge of Django and REST APIs
- Development team is familiar with containerization technologies
- Production environment will have Redis and PostgreSQL available
- Object storage (MinIO/S3) will be configured for file storage
- Monitoring infrastructure will be available for APM integration
