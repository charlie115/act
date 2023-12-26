from django.db import models
from django.utils.timezone import now


class Message(models.Model):
    INFO = "info"
    ERROR = "error"
    MONITOR = "monitor"
    TRADE = "trade"
    MessageTypes = (
        (INFO, "Info"),
        (ERROR, "Error"),
        (MONITOR, "Monitor"),
        (TRADE, "Trade"),
    )

    datetime = models.DateTimeField(default=now)
    telegram_bot_name = models.CharField(max_length=150)
    telegram_chat_id = models.BigIntegerField()
    title = models.CharField(max_length=300)
    content = models.TextField(null=True)
    remarks = models.CharField(max_length=300, null=True)
    origin = models.CharField(max_length=100)
    type = models.CharField(default=INFO, choices=MessageTypes)
    code = models.IntegerField(null=True)
    sent = models.BooleanField(default=False)
    send_count = models.IntegerField(default=1)

    def __str__(self):
        return self.title
