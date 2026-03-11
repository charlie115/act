"""
WSGI config for community_drf project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
from pathlib import Path
from config.path_setup import append_local_apps_path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
append_local_apps_path(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
