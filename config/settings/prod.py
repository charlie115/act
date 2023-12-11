from .base import *  # noqa
from .base import env

DEBUG = False

FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME", default="/api/")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

CORS_ALLOW_ALL_ORIGINS = False

CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", default=[])

INSTALLED_APPS += ("gunicorn",)  # noqa: F405
