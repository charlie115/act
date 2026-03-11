import sys
import os  # Import the os module

from django.conf import settings
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

        # Only start bot services if START_BOT_SERVICES is True
        if settings.START_BOT_SERVICES:
            # Bot services should also start every time the app is started
            # Use RUN_MAIN to avoid running twice in development due to the reloader
            if "runserver" in sys.argv or "daphne" in sys.argv[0]:
                bots = models.ProxySocialApp.objects.filter(provider="telegram")
                for bot in bots:
                    processes = ["telegram_send_message", "telegram_command"]
                    for process in processes:
                        result = subprocess.run(
                            ["pm2", "describe", f"{bot.client_id}.{process}"],
                            capture_output=True,
                            text=True,
                        )
                        if f"{bot.client_id}.{process} doesn't exist" in result.stderr:
                            telegram.start_pm2_process(bot.client_id, process)
                        else:
                            telegram.stop_pm2_process(bot.client_id, process)
                            telegram.delete_pm2_process(bot.client_id, process)
                            telegram.start_pm2_process(bot.client_id, process)
