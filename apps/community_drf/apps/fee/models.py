from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.timezone import now


class FeeRate(models.Model):
    level = models.IntegerField(validators=[MinValueValidator(-1), MaxValueValidator(5)])
    rate = models.DecimalField(max_digits=4, decimal_places=3)
    total_paid_fee_required = models.DecimalField(max_digits=14, decimal_places=2)


class UserFeeLevel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fee_level",
    )
    fee_level = models.IntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(5)], default=1
    )
    total_paid_fee = models.DecimalField(max_digits=14, decimal_places=2)
    last_updated_datetime = models.DateTimeField(default=now)
