from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.timezone import now

from infocore.models import MarketCode
from users.models import User


class ReferralGroup(models.Model):
    name = models.CharField(max_length=150)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    upper_share_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class ReferralCode(models.Model):
    def get_market_codes():
        """Return list of market codes from MarketCode objects."""

        market_codes = [
            (market_code.code, market_code.code)
            for market_code in MarketCode.objects.all()
        ]

        return market_codes

    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="referral_codes",
    )
    referral_group = models.ForeignKey(
        ReferralGroup,
        on_delete=models.CASCADE,
    )
    code = models.TextField(unique=True)
    target_market_code = models.CharField(
        max_length=150,
        choices=get_market_codes(),
        verbose_name="Target Market Code",
    )
    origin_market_code = models.CharField(
        max_length=150,
        choices=get_market_codes(),
        verbose_name="Origin Market Code",
    )
    max_depth = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    contact = models.TextField(
        null=True,
        blank=True,
        help_text="Telegram id or phone number",
    )

    def __str__(self):
        return self.code


class Referral(models.Model):
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE)
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE)
    registered_datetime = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.referred_user} used {self.referral_code}"
