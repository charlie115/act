from urllib.parse import urlparse

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

        if (
            HTTP_X_REAL_IP in node_hostnames
            or HTTP_X_FORWARDED_FOR in node_hostnames
            or REMOTE_ADDR in node_hostnames
        ):
            return (None, None)
        else:
            raise exceptions.AuthenticationFailed("Not authorized.")
