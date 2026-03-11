from django.db import models


class Permission(models.Model):
    """
    This permissions system follows the concept of Django's permissions system
    but not entirely the same as the fields will be used for API management.

    This permission system will still be added in Django admin site, but is mainly used
    during permission checking in APIs.
    """

    name = models.CharField(max_length=255, null=True, blank=True)
    codename = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "API Permission"
