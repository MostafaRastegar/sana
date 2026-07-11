---
name: security-and-auth
description: Secure DRF configuration — JWT lifecycle, permission mapping, input validation, sensitive data protection, CORS, security middleware, error disclosure prevention, rate limiting.
---

# security-and-auth

Secure DRF configuration patterns: JWT lifecycle management, permission-based access control, input validation, sensitive data protection, CORS, security middleware, error disclosure prevention, and rate limiting.

## Usage

Use this skill when configuring auth, permissions, input validation, or any security-sensitive code path.

## Steps

1. **JWT Configuration** — Configure `SIMPLE_JWT` with access tokens ≤60 min lifetime, refresh rotation + blacklist ON, `UPDATE_LAST_LOGIN: True`, `ALGORITHM: "HS256"`. Never hardcode `SIGNING_KEY`.

2. **Permission-Based Access** — Use `ModelActionPermission` on all viewsets for action-to-permission mapping. Custom action permissions via `permission_classes` per action. Model `Meta.permissions` for non-standard actions (archive, export). Minimum: `IsAuthenticated` for every authenticated endpoint.

3. **Input Validation** — `validate_<field>(self, value)` for per-field checks (length, charset, range). `validate(self, attrs)` for cross-field logic; return `super().validate(attrs)`. Reject HTML/script injection in string fields via regex or Django validators.

4. **Sensitive Data** — Use `exclude = ['password', 'last_login']` in serializers. Never return password hashes, tokens, or internal IDs in public responses. Never log request bodies containing password/token fields.

5. **CORS** — `CORS_ALLOWED_ORIGINS` whitelist (never wildcard in prod). `CORS_ALLOW_CREDENTIALS = True`.

6. **Security Middleware** — `SecurityMiddleware` (HSTS, XSS filter, content-type nosniff). `XFrameOptionsMiddleware` with `DENY`. `CsrfViewMiddleware` active for session-authenticated views.

7. **Error Disclosure Prevention** — All errors → structured `DmvnException` response (never stack traces). Generic 500 message to clients, full trace to server logs.

8. **Database Security** — ORM for all queries; no raw SQL with string formatting. If raw SQL unavoidable: `cursor.execute("SELECT ... WHERE id = %s", [id])`.

9. **Rate Limiting** — Configure `DEFAULT_THROTTLE_CLASSES` with `AnonRateThrottle` and `UserRateThrottle`. Set rates: `"anon": "100/hour"`, `"user": "1000/hour"`, `"login": "5/minute"`.

**Checklist:**
- [ ] JWT: short-lived + rotation + blacklist
- [ ] ModelActionPermission on all viewsets
- [ ] All inputs validated at serializer level
- [ ] Sensitive fields excluded from serializers / logs
- [ ] CORS origins whitelisted, no wildcard
- [ ] SecurityMiddleware + XFrameOptionsMiddleware in MIDDLEWARE
- [ ] DmvnException used everywhere (no raw exceptions)
- [ ] ORM-only queries (no string-formatted SQL)
- [ ] Rate limiting configured