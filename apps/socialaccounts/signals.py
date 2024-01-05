import subprocess

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from socialaccounts.models import ProxySocialApp


@receiver(post_save, sender=ProxySocialApp, dispatch_uid="signals.spawn_bot_service")
def spawn_bot_service(sender, instance, created, **kwargs):
    print("spawn_bot_service")

    if created and instance.provider == "telegram":
        subprocess.Popen(
            [
                "pm2",
                "start",
                f"python manage.py telebot {instance.client_id}",
                "--name",
                instance.client_id,
                "--namespace",
                "telebot",
            ]
        )


@receiver(post_delete, sender=ProxySocialApp, dispatch_uid="signals.stop_bot_service")
def stop_bot_service(sender, instance, **kwargs):
    if instance.provider == "telegram":
        subprocess.Popen(
            [
                "pm2",
                "stop",
                instance.client_id,
            ]
        )
        subprocess.Popen(
            [
                "pm2",
                "delete",
                instance.client_id,
            ]
        )
