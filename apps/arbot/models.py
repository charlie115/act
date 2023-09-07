from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ArbotNode(models.Model):
    name = models.CharField(max_length=150)
    domain = models.CharField(max_length=200)
    port = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    telegram_bot_id = models.CharField(max_length=50)
    telegram_bot_token = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class ArbotUserConfig(models.Model):
    BINANCE_MARGIN_MODE_ISOLATED = False
    BINANCE_MARGIN_MODE_CROSS = True

    RISK_WARNING_MODE_DISABLED = 0
    RISK_WARNING_MODE_SEND = 1
    RISK_WARNING_MODE_SEND_AND_EXIT = 2
    RiskWarningModes = (
        (RISK_WARNING_MODE_DISABLED, 0),
        (RISK_WARNING_MODE_SEND, 1),
        (RISK_WARNING_MODE_SEND_AND_EXIT, 2),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="arbot_config"
    )
    node = models.ForeignKey(
        ArbotNode, on_delete=models.RESTRICT, related_name="user_configs"
    )

    service_expiry_date = models.DateTimeField()

    addcir_limit = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        help_text="Format: 000.0000",
    )
    addcir_num_limit = models.IntegerField(blank=True, null=True)

    binance_leverage = models.IntegerField(
        default=4, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    binance_cross = models.BooleanField(default=BINANCE_MARGIN_MODE_ISOLATED)

    risk_warning_mode = models.IntegerField(
        default=RISK_WARNING_MODE_SEND_AND_EXIT, choices=RiskWarningModes
    )
    risk_warning_threshold_p = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MaxValueValidator(0)],
    )

    safe_reverse = models.BooleanField(default=True)

    alarm_num = models.IntegerField(default=1)
    alarm_term_sec = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} @ {self.node.name}"
