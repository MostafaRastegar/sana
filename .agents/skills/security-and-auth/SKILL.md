---
name: security_and_authentication
description: Secure DRF configuration — JWT lifecycle, permission mapping, input validation, sensitive data protection, CORS, security middleware, error disclosure prevention, rate limiting.
---

# Security & Authentication

## When to Use
Use this skill when configuring auth, permissions, input validation, or any security-sensitive code path.

## Standards

### 1. JWT Configuration
```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),       # short-lived
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),          # longer refresh
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,                            # never hardcode
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```
- Access tokens: ≤60 min lifetime
- Refresh rotation + blacklist ON
- Never hardcode SIGNING_KEY

### 2. Permission-Based Access
```python
# ModelActionPermission maps view action → Django permission
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ModelActionPermission]
```
- Custom action permissions via `permission_classes` per action
- Model `Meta.permissions` for non-standard actions (archive, export)
- Fallback: `IsAuthenticated` minimum for every authenticated endpoint

### 3. Input Validation
- `validate_<field>(self, value)` — per-field checks (length, charset, range)
- `validate(self, attrs)` — cross-field logic; return `super().validate(attrs)`
- Reject HTML/script injection in string fields via regex or Django validators

### 4. Sensitive Data
- `exclude = ['password', 'last_login']` in serializers
- Never return password hashes, tokens, or internal IDs in public responses
- Never log request bodies containing password/token fields

### 5. CORS
```python
CORS_ALLOWED_ORIGINS = ["https://yourdomain.com"]  # never wildcard in prod
CORS_ALLOW_CREDENTIALS = True
```

### 6. Security Middleware
- `SecurityMiddleware` (HSTS, XSS filter, content-type nosniff)
- `XFrameOptionsMiddleware` with `DENY`
- `CsrfViewMiddleware` active for session-authenticated views

### 7. Error Disclosure Prevention
- All errors → structured `DmvnException` response (never stack traces)
- Generic 500 message to clients, full trace to server logs

### 8. Database Security
- ORM for all queries; no raw SQL with string formatting
- If raw SQL unavoidable: `cursor.execute("SELECT ... WHERE id = %s", [id])`

### 9. Rate Limiting
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "5/minute",
    },
}
```

## Checklist
- [ ] JWT: short-lived + rotation + blacklist
- [ ] ModelActionPermission on all viewsets
- [ ] All inputs validated at serializer level
- [ ] Sensitive fields excluded from serializers / logs
- [ ] CORS origins whitelisted, no wildcard
- [ ] SecurityMiddleware + XFrameOptionsMiddleware in MIDDLEWARE
- [ ] DmvnException used everywhere (no raw exceptions)
- [ ] ORM-only queries (no string-formatted SQL)
- [ ] Rate limiting configured