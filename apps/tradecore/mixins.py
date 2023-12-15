from urllib.parse import urlsplit, urlunsplit

from django.core.validators import URLValidator


class NodeValidatorMixin(object):
    def validate_domain(self, domain):
        # Only get domain, not full url
        url_parts = urlsplit(domain)
        domain = urlunsplit((url_parts.scheme, url_parts.netloc, "", "", ""))

        # Validate domain
        URLValidator()(domain)

        return domain

    def clean(self):
        cleaned_data = super().clean()
        domain = cleaned_data.get("domain")
        cleaned_data["domain"] = self.validate_domain(domain)

        return cleaned_data
