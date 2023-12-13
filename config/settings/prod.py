from urllib.parse import urljoin

from .base import *  # noqa
from .base import env

DEBUG = False

SCRIPT_NAME = env("DJANGO_SCRIPT_NAME", default="api/")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

CORS_ALLOW_ALL_ORIGINS = False

CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", default=[])

INSTALLED_APPS += ("gunicorn",)  # noqa: F405

# Repeat setting since SCRIPT_NAME can change per environment

STATIC_URL = urljoin(SCRIPT_NAME, "static/")

MEDIA_URL = urljoin(SCRIPT_NAME, "media/")
