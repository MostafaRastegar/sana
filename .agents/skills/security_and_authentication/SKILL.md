---
name: security_and_authentication
description: Brief description of what this skill does
---

# security_and_authentication

Instructions for the AI agent...

## Usage
# Security and Authentication Best Practices

## Overview
This rule defines security best practices for Django REST Framework applications, focusing on authentication, authorization, input validation, and data protection.

## Rule Details

### 1. JWT Authentication Configuration

**Description**: Configure JWT tokens with secure settings and proper lifecycle management.

**Pattern**:
- Set appropriate token lifetimes (short-lived access tokens, longer refresh tokens)
- Enable token rotation and blacklisting
- Use secure signing keys and algorithms
- Implement proper token refresh mechanisms

**Example**:
```python
# GOOD - Secure JWT configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# BAD - Insecure JWT configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),  # Too long
    "ROTATE_REFRESH_TOKENS": False,  # No rotation
    "BLACKLIST_AFTER_ROTATION": False,  # No blacklisting
    "ALGORITHM": "HS256",
    "SIGNING_KEY": "hardcoded-key",  # Hardcoded key
}
```

### 2. Permission-Based Access Control

**Description**: Implement fine-grained permissions using Django's permission system and custom permission classes.

**Pattern**:
- Use `ModelActionPermission` for automatic permission mapping
- Define custom permissions in model Meta class
- Implement custom permission classes for complex scenarios
- Always validate permissions before sensitive operations

**Example**:
```python
# GOOD - Model with custom permissions
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        permissions = [
            ("archive_product", "Can archive product"),
            ("export_product", "Can export product data"),
        ]

# GOOD - Custom permission class
class ProductPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['archive', 'export']:
            return request.user.has_perm('example.archive_product')
        return super().has_permission(request, view)

# BAD - Generic permissions only
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # Too permissive
```

### 3. Input Validation and Sanitization

**Description**: Validate and sanitize all input data to prevent injection attacks and data corruption.

**Pattern**:
- Use serializer validation methods for field-level validation
- Implement cross-field validation in `validate()` method
- Use Django's built-in validators for common patterns
- Sanitize user input before processing

**Example**:
```python
# GOOD - Comprehensive validation
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description']
    
    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        if not re.match(r'^[a-zA-Z0-9\s]+$', value):
            raise serializers.ValidationError("Name contains invalid characters.")
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        if value > 999999:
            raise serializers.ValidationError("Price too high.")
        return value
    
    def validate(self, attrs):
        if attrs.get('name') and attrs.get('description'):
            if attrs['name'].lower() in attrs['description'].lower():
                raise serializers.ValidationError("Name should not be in description.")
        return super().validate(attrs)

# BAD - No validation
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
```

### 4. Sensitive Data Protection

**Description**: Protect sensitive data in serializers, responses, and logs.

**Pattern**:
- Use `read_only_fields` for sensitive data
- Exclude sensitive fields from serializers
- Never log sensitive information
- Use field-level permissions for sensitive data access

**Example**:
```python
# GOOD - Protect sensitive data
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 
            'last_name', 'full_name', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

# GOOD - Exclude sensitive fields
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ['created_by', 'updated_at']  # Exclude sensitive fields

# BAD - Expose all fields
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # Exposes password, sensitive data
```

### 5. CORS and Cross-Origin Security

**Description**: Configure CORS properly to prevent cross-origin attacks while allowing legitimate requests.

**Pattern**:
- Use specific allowed origins instead of wildcards
- Configure appropriate CORS headers
- Disable credentials if not needed
- Implement proper CSRF protection

**Example**:
```python
# GOOD - Secure CORS configuration
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# BAD - Insecure CORS
CORS_ALLOWED_ORIGINS = ["*"]  # Wildcard - too permissive
CORS_ALLOW_CREDENTIALS = False  # Should be True if using auth
```

### 6. Security Headers and Middleware

**Description**: Implement security headers and middleware to protect against common web vulnerabilities.

**Pattern**:
- Use security middleware for XSS, CSRF, and clickjacking protection
- Configure appropriate security headers
- Implement rate limiting for API endpoints
- Use HTTPS in production

**Example**:
```python
# GOOD - Security middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# GOOD - Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# BAD - Missing security middleware
MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Missing security middleware
]
```

### 7. Error Handling and Information Disclosure

**Description**: Handle errors securely without exposing sensitive information.

**Pattern**:
- Use structured error responses with appropriate status codes
- Avoid exposing stack traces or internal errors to clients
- Log errors securely without sensitive data
- Use custom exception handler for consistent error responses

**Example**:
```python
# GOOD - Custom exception handler
def custom_exception_handler(exc, context):
    if isinstance(exc, DmvnException):
        return Response({
            'error': {
                'status_code': exc.status_code,
                'code': exc.code,
                'message': _(exc.message),
                'details': exc.details or [],
            }
        }, status=exc.status_code)
    
    # Generic error response
    return Response({
        'error': {
            'status_code': 500,
            'code': 'internal_error',
            'message': 'An unexpected error occurred.',
            'details': [],
        }
    }, status=500)

# BAD - Expose internal errors
def bad_exception_handler(exc, context):
    return Response({
        'error': str(exc),  # Exposes internal details
        'traceback': traceback.format_exc(),  # Exposes stack trace
    }, status=500)
```

### 8. Database Security

**Description**: Implement database security best practices to prevent SQL injection and data leaks.

**Pattern**:
- Use Django ORM instead of raw SQL queries
- Implement proper database permissions
- Use parameterized queries when raw SQL is necessary
- Validate and sanitize all database inputs

**Example**:
```python
# GOOD - Use ORM
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)  # Safe ORM query
        return queryset

# GOOD - Parameterized raw query (if necessary)
def get_products_by_category(category_id):
    return Product.objects.raw(
        "SELECT * FROM example_product WHERE category_id = %s",
        [category_id]  # Parameterized
    )

# BAD - Raw SQL with string formatting
def get_products_by_category(category_id):
    return Product.objects.raw(
        f"SELECT * FROM example_product WHERE category_id = {category_id}"  # Unsafe
    )
```

### 9. Authentication Security

**Description**: Implement secure authentication patterns and session management.

**Pattern**:
- Use JWT for stateless authentication
- Implement proper token refresh mechanisms
- Use secure session settings
- Implement account lockout for failed login attempts

**Example**:
```python
# GOOD - Secure session settings
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# GOOD - JWT token refresh endpoint
class TokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Add additional security checks if needed
        return super().post(request, *args, **kwargs)

# BAD - Insecure session settings
SESSION_COOKIE_SECURE = False  # Can be sent over HTTP
SESSION_COOKIE_HTTPONLY = False  # Accessible via JavaScript
```

### 10. API Rate Limiting

**Description**: Implement rate limiting to prevent abuse and DoS attacks.

**Pattern**:
- Use Django REST Framework's throttle classes
- Implement different rate limits for different endpoints
- Use caching for rate limit storage
- Monitor and log rate limit violations

**Example**:
```python
# GOOD - Rate limiting configuration
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
    }
}

# GOOD - Custom throttle for sensitive endpoints
class SensitiveActionThrottle(UserRateThrottle):
    scope = 'sensitive_actions'

class ProductViewSet(viewsets.ModelViewSet):
    throttle_classes = [SensitiveActionThrottle]
    
    @action(detail=True, methods=['patch'])
    def archive(self, request, pk=None):
        # Implementation

# BAD - No rate limiting
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    # No throttle classes
}
```

## Implementation Guidelines

1. **Defense in Depth**: Implement multiple layers of security
2. **Principle of Least Privilege**: Grant minimum necessary permissions
3. **Input Validation**: Validate all inputs at multiple layers
4. **Error Handling**: Handle errors securely without information disclosure
5. **Logging**: Log security events without sensitive data
6. **Regular Audits**: Regularly review and update security configurations

## Security Checklist

- [ ] JWT tokens have appropriate lifetimes and rotation
- [ ] All endpoints have proper permission classes
- [ ] Input validation is implemented at serializer level
- [ ] Sensitive data is excluded from responses
- [ ] CORS is configured with specific origins
- [ ] Security headers are properly configured
- [ ] Error responses don't expose internal details
- [ ] Database queries use ORM or parameterized queries
- [ ] Session settings are secure
- [ ] Rate limiting is implemented for sensitive endpoints
- [ ] Regular security audits are performed