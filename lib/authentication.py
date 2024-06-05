from urllib.parse import urlparse

from django.conf import settings
from rest_framework import authentication, exceptions

from tradecore.models import Node


class NodeIPAuthentication(authentication.BaseAuthentication):
    """Only authenticate Node IPs"""

    def authenticate(self, request):
        HTTP_X_REAL_IP = request.META.get("HTTP_X_REAL_IP", None)
        HTTP_X_FORWARDED_FOR = request.META.get("HTTP_X_FORWARDED_FOR", None)
        REMOTE_ADDR = request.META.get("REMOTE_ADDR", None)

        node_urls = list(Node.objects.values_list("url", flat=True))
        node_hostnames = [urlparse(url).hostname for url in node_urls]

        authorized_ips = node_hostnames + settings.CORE_IPS

        if (
            HTTP_X_REAL_IP in authorized_ips
            or HTTP_X_FORWARDED_FOR in authorized_ips
            or REMOTE_ADDR in authorized_ips
        ):
            return (None, None)
        else:
            raise exceptions.AuthenticationFailed("Not authorized.")
