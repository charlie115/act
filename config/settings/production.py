import dj_database_url

from .base import *  # noqa


ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

CORS_ALLOW_ALL_ORIGINS = False

CORS_ORIGIN_WHITELIST = env.list('CORS_ORIGIN_WHITELIST', default=[])

INSTALLED_APPS += (
    "gunicorn",
)

DATABASES = {
    'default': dj_database_url.config(
        default=env('COMMUNITY_DB_URL'),
        conn_max_age=600
    ),
}
