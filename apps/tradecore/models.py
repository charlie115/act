from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Node(models.Model):
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


class UserConfig(models.Model):
    BINANCE_MARGIN_MODE_ISOLATED = False
    BINANCE_MARGIN_MODE_CROSS = True

    RISK_WARNING_MODE_DISABLED = 0
    RISK_WARNING_MODE_SEND = 1
    RISK_WARNING_MODE_SEND_AND_EXIT = 2
    RiskWarningModes = (
        (RISK_WARNING_MODE_DISABLED, "Disabled"),
        (RISK_WARNING_MODE_SEND, "Send warning"),
        (RISK_WARNING_MODE_SEND_AND_EXIT, "Send warning and exit entered trades"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_config"
    )

    service_expiry_date = models.DateTimeField(
        help_text="If a user makes a payment for the subscription, the `service_expiry_date` will be extended."
    )

    addcir_limit = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        help_text="A number that should be applied in the Arbot core when it runs the addcir feature.<br>"
        "Format: `000.0000`",
    )
    addcir_num_limit = models.IntegerField(
        blank=True,
        null=True,
        help_text="A number that should be applied in the Arbot core when it runs the addcir feature.",
    )

    binance_leverage = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Leverage to use when executing trades in Binance.",
    )
    binance_cross = models.BooleanField(
        default=BINANCE_MARGIN_MODE_ISOLATED,
        help_text="Whether Binance Margin mode is cross (or isolated).",
    )

    risk_warning_mode = models.IntegerField(
        default=RISK_WARNING_MODE_SEND_AND_EXIT, choices=RiskWarningModes
    )
    risk_warning_threshold_p = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MaxValueValidator(0)],
        help_text="If the unrealized loss goes below the risk warning threshold, "
        "risk warning function is getting executed according to the setting. <br>"
        "`risk_warning_threshold_p` value should be set to *less than 0*. "
        "But when it's set to `null`, it has a special meaning.<br>"
        "`null`: When margin_call signal is sent",
    )

    safe_reverse = models.BooleanField(
        default=True, help_text="Whether to turn on reverse trade."
    )

    alarm_num = models.IntegerField(
        default=1,
        help_text="When a user receives a telegram message from the telegram bot, a user can configure the bot "
        "to send more than one message about the same event so that a user (e.g. sleeping) can be alarmed enough.",
    )
    alarm_term_sec = models.IntegerField(
        default=1,
        help_text="Related to the alarm_num. "
        "A user can also configure the term between messages if the user has set the alarm_num bigger than 1.",
    )

    def __str__(self):
        return f"{self.user.username} config"

    class Meta:
        verbose_name = "User Config"
