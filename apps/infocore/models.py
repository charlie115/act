from django.db import models
from django.utils.timezone import now


class Asset(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    icon = models.ImageField(upload_to="assets/icons/")
    last_update = models.DateTimeField(default=now)

    def __str__(self):
        return self.symbol
