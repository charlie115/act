from django.apps import AppConfig


class SocialaccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "socialaccounts"
    verbose_name = "Social Account"

    def ready(self):
        from . import signals  # noqa: F401
