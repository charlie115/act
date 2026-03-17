from urllib.parse import urljoin

from .base import *  # noqa
from .base import env
from config.runtime_validation import validate_prod_hosts

DEBUG = False

SCRIPT_NAME = env("DJANGO_SCRIPT_NAME", default="api/")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
validate_prod_hosts(env, ALLOWED_HOSTS)

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", default=[])

INSTALLED_APPS += ("gunicorn",)  # noqa: F405

# Repeat setting since SCRIPT_NAME can change per environment

STATIC_URL = urljoin(SCRIPT_NAME, "static/")

MEDIA_URL = urljoin(SCRIPT_NAME, "media/")

# Security: ensure cookies are only sent over HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
