# System Patterns

## Architecture Overview

Team Backend follows Django's MTV (Model-Template-View) pattern with REST API extensions, implementing a layered architecture that promotes separation of concerns and maintainability.

## Current State (Updated: February 17, 2026)

### Project Architecture Status
- **Framework**: Django 5.2.9 with Django REST Framework 3.16.0
- **Architecture Pattern**: Layered architecture with clear separation of concerns
- **App Structure**: Modular design with core utilities and shared components
- **Recent Changes**: Streamlined middleware, updated permissions, enhanced type safety

### Implemented Architecture Components

#### 1. Core Module Architecture
- **Status**: ✅ Core utilities fully implemented
- **Components**: Exception handling, middleware, permissions, serializers, pagination
- **Features**: HTTP method restriction, language detection, model-based permissions

#### 2. REST API Layer
- **Status**: ✅ API infrastructure configured
- **Components**: DRF ViewSets, custom pagination, schema generation
- **Features**: Auto-generated documentation, language support, structured responses

#### 3. Background Task System
- **Status**: ✅ Celery integration complete
- **Components**: Task queues, beat scheduling, Redis broker
- **Features**: Dedicated queues, task routing, monitoring support

#### 4. Security Layer
- **Status**: ✅ Security measures implemented
- **Components**: JWT authentication, CORS, middleware security
- **Features**: Token management, method restrictions, input validation

## Key Architectural Patterns

### 1. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
├─────────────────────────────────────────────────────────────┤
│  API Views (DRF ViewSets)  │  Admin Interface  │  Templates │
├─────────────────────────────────────────────────────────────┤
│                      Service Layer                          │
├─────────────────────────────────────────────────────────────┤
│  Serializers  │  Permissions  │  Pagination  │  Validation  │
├─────────────────────────────────────────────────────────────┤
│                      Data Access Layer                      │
├─────────────────────────────────────────────────────────────┤
│  Models  │  Managers  │  QuerySets  │  Database Migrations  │
├─────────────────────────────────────────────────────────────┤
│                      Infrastructure                        │
├─────────────────────────────────────────────────────────────┤
│  Celery Tasks  │  Storage  │  Caching  │  Logging  │  APM    │
└─────────────────────────────────────────────────────────────┘
```

### 2. Django App Structure

The project is organized into Django apps following the single responsibility principle:

- **core**: Shared utilities, middleware, base classes, and common functionality
- **accounts**: User management, authentication, and authorization (planned)
- **api**: REST API endpoints, serializers, and API-specific logic (planned)

### 3. REST API Design Patterns

#### Resource-Based Endpoints
- Follow REST conventions with proper HTTP methods
- Use Django REST Framework ViewSets for consistency
- Implement proper HTTP status codes for all responses
- Support filtering, searching, and ordering out of the box

#### Response Format
```json
{
  "success": true,
  "data": { /* resource data */ },
  "message": "Operation completed successfully",
  "meta": {
    "pagination": { /* pagination info */ },
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### Error Response Format
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "field_name": ["Error message"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

## Design Patterns Implementation

### 1. Repository Pattern (Models)

Models serve as the repository layer, encapsulating database operations:

```python
class UserManager(BaseUserManager):
    """Custom user manager with business logic."""
    
    def create_user(self, email, password=None, **extra_fields):
        # Business logic for user creation
        pass

class User(AbstractBaseUser):
    """User model with custom fields and methods."""
    
    objects = UserManager()
    
    def get_full_name(self):
        # Business logic for full name
        pass
```

### 2. Service Layer Pattern (Views)

Views act as the service layer, orchestrating operations between models and serializers:

```python
class UserViewSet(ModelViewSet):
    """User API endpoints with business logic orchestration."""
    
    def create(self, request, *args, **kwargs):
        # Business logic orchestration
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call model methods
        user = serializer.save()
        
        # Return response
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### 3. Factory Pattern (Serializers)

Serializers use factory patterns for complex object creation:

```python
class UserSerializer(serializers.ModelSerializer):
    """User serializer with custom field handling."""
    
    profile_picture = serializers.ImageField(
        max_length=None, 
        use_url=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'profile_picture']
```

### 4. Observer Pattern (Signals)

Django signals implement the observer pattern for decoupled event handling:

```python
@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handle user creation events."""
    if created:
        # Send welcome email
        # Create default team
        # Log activity
        pass
```

### 5. Strategy Pattern (Authentication)

Multiple authentication strategies are supported through Django's authentication backends:

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]
```

## Critical Implementation Paths

### 1. User Authentication Flow

```
1. User Registration
   ├── Validate input data
   ├── Create user instance
   ├── Send verification email (optional)
   └── Return success response

2. User Login
   ├── Validate credentials
   ├── Generate JWT tokens
   ├── Set refresh token in HTTP-only cookie
   └── Return access token

3. Token Refresh
   ├── Validate refresh token
   ├── Generate new access token
   ├── Rotate refresh token (optional)
   └── Return new tokens

4. Logout
   ├── Blacklist current tokens
   ├── Clear refresh token cookie
   └── Return success response
```

### 2. File Upload Flow

```
1. File Upload Request
   ├── Validate file type and size
   ├── Generate unique filename
   └── Store in temporary location

2. File Processing
   ├── Move to permanent storage
   ├── Generate secure URL
   ├── Update database record
   └── Trigger background processing

3. File Access
   ├── Validate permissions
   ├── Generate signed URL (if private)
   └── Return file URL

4. File Cleanup
   ├── Identify expired files
   ├── Remove from storage
   └── Clean up database records
```

### 3. Team Management Flow

```
1. Team Creation
   ├── Validate team data
   ├── Create team instance
   ├── Set creator as admin
   └── Return team details

2. Member Invitation
   ├── Validate invitation data
   ├── Create invitation record
   ├── Send invitation email
   └── Return invitation details

3. Member Management
   ├── Validate role changes
   ├── Update member permissions
   ├── Log activity
   └── Notify affected users

4. Team Deletion
   ├── Validate permissions
   ├── Archive related data
   ├── Delete team record
   └── Notify members
```

## Database Design Patterns

### 1. Soft Delete Pattern

Models implement soft deletion to preserve data integrity:

```python
class BaseModel(models.Model):
    """Base model with soft delete support."""
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = BaseManager()
    all_objects = models.Manager()
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete implementation."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
```

### 2. Audit Trail Pattern

Models track creation and modification history:

```python
class BaseModel(models.Model):
    """Base model with audit trail."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(class)s_updated'
    )
```

### 3. Polymorphic Models

For flexible data modeling:

```python
class TeamMember(models.Model):
    """Base team member model."""
    
    class MemberType(models.TextChoices):
        USER = 'user', 'User'
        GROUP = 'group', 'Group'
    
    member_type = models.CharField(max_length=10, choices=MemberType.choices)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    class Meta:
        abstract = True
```

## Caching Strategies

### 1. Redis Caching

```python
# Cache frequently accessed data
from django.core.cache import cache

def get_team_members(team_id):
    cache_key = f"team_members_{team_id}"
    members = cache.get(cache_key)
    
    if not members:
        members = TeamMember.objects.filter(team_id=team_id)
        cache.set(cache_key, members, timeout=300)  # 5 minutes
    
    return members
```

### 2. Database Query Optimization

```python
# Use select_related and prefetch_related
def get_team_with_members(team_id):
    return Team.objects.select_related('created_by').prefetch_related(
        'members__user',
        'members__permissions'
    ).get(id=team_id)
```

## Background Task Patterns

### 1. Celery Task Organization

```python
# Dedicated queues for different task types
CELERY_TASK_ROUTES = {
    'activity_log.tasks.log_activity_async': {'queue': 'activity_logs'},
    'api.tasks.cleanup_s3_temp_files': {'queue': 'celery4'},
}
```

### 2. Task Retry and Error Handling

```python
@app.task(bind=True, max_retries=3)
def process_file_upload(self, file_id):
    try:
        # Process file
        pass
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        else:
            # Handle permanent failure
            pass
```

## Security Patterns

### 1. Input Validation

```python
class UserSerializer(serializers.ModelSerializer):
    """User serializer with comprehensive validation."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[
        MinLengthValidator(6),
        StrongPasswordValidator()
    ])
    
    def validate_email(self, value):
        # Custom email validation
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
```

### 2. Permission Classes

```python
class IsTeamAdmin(permissions.BasePermission):
    """Permission class for team admin operations."""
    
    def has_object_permission(self, request, view, obj):
        return obj.members.filter(
            user=request.user,
            role='admin'
        ).exists()
```

## Error Handling Patterns

### 1. Custom Exception Handler

```python
def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses."""
    
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data['success'] = False
        response.data['error_code'] = exc.__class__.__name__
    
    return response
```

### 2. Validation Error Handling

```python
class BaseViewSet(ModelViewSet):
    """Base viewset with enhanced error handling."""
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': exc.detail,
                'error_code': 'VALIDATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().handle_exception(exc)
```

## Recent Architecture Improvements

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

These patterns ensure the application is maintainable, scalable, and follows Django best practices while providing a robust foundation for team management functionality.
