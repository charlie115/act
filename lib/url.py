from django.conf import settings
from urllib.parse import urljoin


def mkpath(path):
    return urljoin(settings.SCRIPT_NAME, path)
