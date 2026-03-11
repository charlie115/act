from datetime import timedelta
from urllib.parse import urljoin

from .base import *  # noqa


DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS += ("django_extensions",)  # noqa: F405

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [  # noqa: F405
    "rest_framework.authentication.SessionAuthentication"
]

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(days=5)  # noqa: F405

# Repeat setting since SCRIPT_NAME can change per environment

STATIC_URL = urljoin(SCRIPT_NAME, "static/")  # noqa: F405

MEDIA_URL = urljoin(SCRIPT_NAME, "media/")  # noqa: F405
