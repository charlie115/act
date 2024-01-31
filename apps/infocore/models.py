from django.db import models
from django.utils.timezone import now


class Asset(models.Model):
    symbol = models.CharField(max_length=30, unique=True)
    icon = models.ImageField(upload_to="assets/icons/")
    note = models.CharField(max_length=300, blank=True)
    last_update = models.DateTimeField(default=now)

    def __str__(self):
        return self.symbol


class MarketCode(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Market Code"
