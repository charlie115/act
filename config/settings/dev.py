from datetime import timedelta

from .base import *  # noqa


DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS += ("django_extensions",)  # noqa: F405

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [  # noqa: F405
    "rest_framework.authentication.SessionAuthentication"
]

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=60)  # noqa: F405
