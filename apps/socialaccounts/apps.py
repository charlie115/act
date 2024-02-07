import sys

from django.apps import AppConfig


class SocialaccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "socialaccounts"
    verbose_name = "Social Account"

    def ready(self):
        import subprocess
        from . import signals  # noqa: F401
        from . import models
        from . import telegram

        # Bot services should also start every time the app is started
        if "runserver" in sys.argv or "daphne" in sys.argv[0]:
            bots = models.ProxySocialApp.objects.filter(provider="telegram")
            for bot in bots:
                result = subprocess.run(
                    ["pm2", "describe", bot.client_id],
                    capture_output=True,
                    text=True,
                )
                if f"{bot.client_id} doesn't exist" in result.stderr:
                    telegram.start_pm2_process(bot.client_id)
