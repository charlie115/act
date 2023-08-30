from datetime import timedelta

from .base import *  # noqa


DEBUG = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS += ("django_extensions", )  # noqa: F405

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += [
    'rest_framework.authentication.SessionAuthentication'
]

SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=60)
