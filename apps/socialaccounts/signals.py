import subprocess

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from socialaccounts.models import ProxySocialApp


@receiver(pre_save, sender=ProxySocialApp, dispatch_uid="signals.update_bot_service")
def update_bot_service(sender, instance, **kwargs):
    if instance.provider == "telegram":
        try:
            original = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            if original.client_id != instance.client_id:
                subprocess.Popen(
                    [
                        "pm2",
                        "stop",
                        original.client_id,
                    ]
                )
                subprocess.Popen(
                    [
                        "pm2",
                        "delete",
                        original.client_id,
                    ]
                )
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


@receiver(post_save, sender=ProxySocialApp, dispatch_uid="signals.spawn_bot_service")
def spawn_bot_service(sender, instance, created, **kwargs):
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


@receiver(post_delete, sender=ProxySocialApp, dispatch_uid="signals.remove_bot_service")
def remove_bot_service(sender, instance, **kwargs):
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
