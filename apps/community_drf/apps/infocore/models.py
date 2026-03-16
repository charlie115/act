from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now

from users.models import User


class Asset(models.Model):
    symbol = models.CharField(max_length=30, unique=True)
    icon = models.ImageField(upload_to="assets/icons/")
    note = models.CharField(max_length=300, blank=True)
    last_update = models.DateTimeField(default=now)
    icon_fetch_failures = models.PositiveSmallIntegerField(default=0)
    icon_fetch_last_attempt_at = models.DateTimeField(null=True, blank=True)
    icon_fetch_last_error = models.CharField(max_length=500, blank=True)

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


class VolatilityNotificationConfig(models.Model):
    """
    User configuration for volatility-based notifications.
    When volatility (mean_diff) exceeds the threshold, a notification message
    is created and sent via Telegram.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="volatility_notification_configs",
    )

    # Market combination
    target_market_code = models.CharField(
        max_length=150,
        help_text="Target market code, e.g., 'UPBIT_SPOT/KRW'",
    )
    origin_market_code = models.CharField(
        max_length=150,
        help_text="Origin market code, e.g., 'BINANCE_USD_M/USDT'",
    )

    # Optional: specific base assets to monitor
    base_assets = models.JSONField(
        null=True,
        blank=True,
        help_text='List of base assets to monitor, e.g., ["BTC", "ETH"]. '
        "Leave empty to monitor all assets in the market combination.",
    )

    # Volatility threshold (mean_diff value)
    volatility_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        validators=[MinValueValidator(0)],
        help_text="Trigger notification when mean_diff >= this value. "
        "Example: 0.05 means 5% volatility.",
    )

    # Notification interval in minutes (prevents spam)
    notification_interval_minutes = models.PositiveIntegerField(
        default=180,  # 3 hours default
        validators=[MinValueValidator(1)],
        help_text="Minimum minutes between notifications for this config.",
    )

    # State tracking
    enabled = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.target_market_code}:{self.origin_market_code}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_market_code", "origin_market_code"],
                name="unique_user_market_combination",
            )
        ]
        verbose_name = "Volatility Notification Config"
        verbose_name_plural = "Volatility Notification Configs"


class VolatilityNotificationHistory(models.Model):
    """
    Tracks per-symbol notification history to prevent duplicate notifications
    within the configured interval.
    """

    config = models.ForeignKey(
        VolatilityNotificationConfig,
        on_delete=models.CASCADE,
        related_name="notification_history",
    )
    base_asset = models.CharField(max_length=30)
    notified_at = models.DateTimeField(auto_now_add=True)
    mean_diff = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="The volatility value when notification was sent.",
    )

    def __str__(self):
        return f"{self.config.id} - {self.base_asset} @ {self.notified_at}"

    class Meta:
        indexes = [
            models.Index(fields=["config", "base_asset", "notified_at"]),
        ]
        verbose_name = "Volatility Notification History"
        verbose_name_plural = "Volatility Notification Histories"
