from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.timezone import now


class Message(models.Model):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    MONITOR = "MONITOR"
    TRADE = "TRADE"
    COMMAND = "COMMAND"
    MessageTypes = (
        (INFO, "INFO"),
        (WARNING, "WARNING"),
        (ERROR, "ERROR"),
        (MONITOR, "MONITOR"),
        (TRADE, "TRADE"),
        (COMMAND, "COMMAND"),
    )

    datetime = models.DateTimeField(default=now)
    telegram_bot_username = models.CharField(max_length=150)
    telegram_chat_id = models.BigIntegerField()
    title = models.CharField(max_length=300)
    content = models.TextField(null=True, blank=True)
    remarks = models.CharField(max_length=300, null=True, blank=True)
    origin = models.CharField(max_length=100)
    type = models.CharField(default=INFO, choices=MessageTypes)
    code = models.IntegerField(null=True, blank=True)
    sent = models.BooleanField(default=False)
    send_times = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Number of times the message should be sent",
    )
    send_term = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="The interval between messages if sent more than 1 time\n(in seconds)",
    )
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.title
