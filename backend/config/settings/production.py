DEBUG = False
from .base import *
import os

# Production settings

# Production security
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Security middleware
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

trusted_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")

if trusted_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in trusted_origins.split(",")]
else:
    CSRF_TRUSTED_ORIGINS = []

# Database
if DATABASE_URL:
    DATABASES = {"default": env.db()}
    DATABASES["default"]["CONN_MAX_AGE"] = 0
    DATABASES["default"]["OPTIONS"] = {
        "pool": {
            "min_size": 1,
            "max_size": 10,
            "timeout": 300,
            "max_lifetime": 3600,
            "max_idle": 600,
        }
    }

    CONN_MAX_AGE = os.environ.get("CONN_MAX_AGE", 0)
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Redis cache (if available)
if os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL"),
        }
    }

# Production CORS
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

# Object Storage Configuration (MinIO) - Modern STORAGES setting
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Static files finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
MEDIA_URL = f'{os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")}/{os.environ.get("MINIO_BUCKET_NAME", "my-local-bucket")}/'
# Production logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "/var/app.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
