from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from rest_framework import authentication, exceptions

from tradecore.models import Node

NODE_IP_CACHE_KEY = "node_ip_auth:authorized_ips"
NODE_IP_CACHE_TTL = 60  # seconds


class NodeIPAuthentication(authentication.BaseAuthentication):
    """Only authenticate Node IPs"""

    def authenticate(self, request):
        REMOTE_ADDR = request.META.get("REMOTE_ADDR", None)

        authorized_ips = cache.get(NODE_IP_CACHE_KEY)
        if authorized_ips is None:
            node_urls = list(Node.objects.values_list("url", flat=True))
            node_hostnames = [urlparse(url).hostname for url in node_urls]
            authorized_ips = node_hostnames + settings.CORE_IPS
            cache.set(NODE_IP_CACHE_KEY, authorized_ips, NODE_IP_CACHE_TTL)

        if REMOTE_ADDR in authorized_ips:
            return (None, None)
        else:
            return None
