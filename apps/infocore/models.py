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
    SPOT = "SPOT"
    USD_M = "USD_M"
    COIN_M = "COIN_M"
    FUTURES = "FUTURES"
    MarketTypes = [
        (SPOT, SPOT),
        (USD_M, USD_M),
        (COIN_M, COIN_M),
        (FUTURES, FUTURES),
    ]

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=150, unique=True)
    type = models.CharField(choices=MarketTypes)

    def save(self, *args, **kwargs):
        pk = self.pk
        if pk is None:
            self.type = MarketCode.get_type(self.code)

        super(MarketCode, self).save(*args, **kwargs)

    def __str__(self):
        return self.code

    @staticmethod
    def get_type(code):
        return "SPOT" if "SPOT" in code else "FUTURES"

    class Meta:
        verbose_name = "Market Code"
