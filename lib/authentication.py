from rest_framework import authentication, exceptions
from django.conf import settings


class CoreIPAuthentication(authentication.BaseAuthentication):
    """Authenticate if ip is an infocore server ip"""

    def authenticate(self, request):
        if (
            request.META.get("HTTP_X_REAL_IP", None) in settings.INFOCORE_IPS
            or request.META.get("HTTP_X_FORWARDED_FOR", None) in settings.INFOCORE_IPS
            or request.META.get("REMOTE_ADDR", None) in settings.INFOCORE_IPS
        ):
            return (None, None)
        else:
            raise exceptions.AuthenticationFailed("Not authorized.")
