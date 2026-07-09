import os
from .base import *

# Test settings
DEBUG = False

SECRET_KEY = 'django-insecure-test-key'

# Test database (SQLite for speed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
USE_TZ = True

# Test-specific settings
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Fast but insecure - only for testing
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Celery settings for testing (use eager mode)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = True

# Disable APM in tests
if 'elasticapm.contrib.django' in INSTALLED_APPS:
    INSTALLED_APPS.remove('elasticapm.contrib.django')
