from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.core.cache import cache

from users.models import User, UserBlocklist, UserProfile


@receiver(post_save, sender=User, dispatch_uid="signals.create_user_profile")
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile for every new User."""

    if created:
        UserProfile.objects.create(user=instance)


@receiver(pre_save, sender=User, dispatch_uid="signals.update_last_username_change")
def update_last_username_change(sender, instance, **kwargs):
    """Update last_username_change whenever username is changed."""

    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if not original.username == instance.username:
            from django.utils.timezone import now

            instance.last_username_change = now()


@receiver(
    post_save, sender=UserBlocklist, dispatch_uid="signals.add_user_to_blocklist_cache"
)
@receiver(
    post_delete,
    sender=UserBlocklist,
    dispatch_uid="signals.delete_user_from_blocklist_cache",
)
def add_user_to_blocklist_cache(sender, **kwargs):
    cache.set(settings.REDIS_CHAT_BLOCKLIST_KEY, list(sender.objects.all()), timeout=None)
