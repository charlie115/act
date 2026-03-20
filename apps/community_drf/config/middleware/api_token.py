"""
API Token Middleware — validates HMAC-signed short-lived tokens on infocore endpoints.

Token format: ``{timestamp_hex}.{hmac_sha256_signature}``

The same shared secret (``API_TOKEN_SECRET`` env var) must be configured
in both the Next.js frontend and this Django backend.

- Tokens expire after 5 minutes.
- Only applied to ``/infocore/`` paths.
- Bypassed when ``DEBUG=True`` and no token is provided (dev convenience).
- Authenticated requests (with valid JWT/session) bypass the check.
"""

import hashlib
import hmac
import time

from django.conf import settings
from django.http import JsonResponse


SECRET = getattr(settings, "API_TOKEN_SECRET", None)
TTL_SECONDS = 5 * 60  # 5 minutes
PROTECTED_SEGMENT = "/infocore/"


class ApiTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only protect paths containing /infocore/ (handles SCRIPT_NAME prefix like /api/infocore/)
        if PROTECTED_SEGMENT not in request.path:
            return self.get_response(request)

        # Authenticated users (JWT/session) bypass token check
        if hasattr(request, "user") and request.user.is_authenticated:
            return self.get_response(request)

        # In DEBUG mode without a secret configured, skip enforcement
        if settings.DEBUG and not SECRET:
            return self.get_response(request)

        # If no secret configured in production, deny all anonymous requests
        if not SECRET:
            return JsonResponse({"detail": "API token not configured."}, status=500)

        token = request.META.get("HTTP_X_API_TOKEN", "")

        if not token:
            return JsonResponse(
                {"detail": "Missing API token."},
                status=403,
            )

        if not self._validate_token(token):
            return JsonResponse(
                {"detail": "Invalid or expired API token."},
                status=403,
            )

        return self.get_response(request)

    @staticmethod
    def _validate_token(token):
        try:
            parts = token.split(".", 1)
            if len(parts) != 2:
                return False

            timestamp_hex, signature = parts
            timestamp_ms = int(timestamp_hex, 16)

            # Check expiry
            now_ms = int(time.time() * 1000)
            if abs(now_ms - timestamp_ms) > TTL_SECONDS * 1000:
                return False

            # Verify HMAC
            expected = hmac.new(
                SECRET.encode(),
                str(timestamp_ms).encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected)
        except (ValueError, TypeError, AttributeError):
            return False
