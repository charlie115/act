from urllib.parse import urlsplit, urlunsplit
from django.core.validators import URLValidator


class ArbotNodeValidatorMixin(object):

    def validate_domain(self, domain):
        # Only get domain, not full url
        url_parts = urlsplit(domain)
        domain = urlunsplit((url_parts.scheme, url_parts.netloc, "", "", ""))

        # Validate domain
        URLValidator()(domain)

        return domain
