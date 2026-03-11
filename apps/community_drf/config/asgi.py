"""
ASGI config for community_drf project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import sys

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

asgi_application = get_asgi_application()

from . import routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": asgi_application,
        "websocket": routing.websocket_urlpatterns,
    }
)
