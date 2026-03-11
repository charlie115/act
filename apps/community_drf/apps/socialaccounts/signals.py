from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from socialaccounts.models import ProxySocialApp
from socialaccounts.telegram import (
    start_pm2_process,
    stop_pm2_process,
    delete_pm2_process,
)


@receiver(pre_save, sender=ProxySocialApp, dispatch_uid="signals.update_bot_service")
def update_bot_service(sender, instance, **kwargs):
    if instance.provider == "telegram":
        try:
            original = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            if original.client_id != instance.client_id:
                stop_pm2_process(original.client_id)
                delete_pm2_process(original.client_id)
                start_pm2_process(instance.client_id, "telegram_send_message")
                start_pm2_process(instance.client_id, "telegram_command")


@receiver(post_save, sender=ProxySocialApp, dispatch_uid="signals.spawn_bot_service")
def spawn_bot_service(sender, instance, created, **kwargs):
    if created and instance.provider == "telegram":
        start_pm2_process(instance.client_id, "telegram_send_message")
        start_pm2_process(instance.client_id, "telegram_command")


@receiver(post_delete, sender=ProxySocialApp, dispatch_uid="signals.remove_bot_service")
def remove_bot_service(sender, instance, **kwargs):
    if instance.provider == "telegram":
        stop_pm2_process(instance.client_id)
        delete_pm2_process(instance.client_id)
