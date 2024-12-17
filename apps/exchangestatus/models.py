from django.db import models
from django.utils import timezone
from infocore.models import MarketCode

class ExchangeServerStatus(models.Model):
    """
    Represents a server check (maintenance/downtime) for a specific market (exchange).
    Only one record per MarketCode is allowed.
    """
    market_code = models.ForeignKey(
        MarketCode,
        on_delete=models.CASCADE,
        related_name='server_statuses'
    )
    start_time = models.DateTimeField(help_text="Server check start time")
    end_time = models.DateTimeField(help_text="Server check end time")
    message = models.CharField(max_length=255, null=True, blank=True, help_text="Optional message describing the downtime")

    class Meta:
        verbose_name = "Exchange Server Status"
        verbose_name_plural = "Exchange Server Statuses"
        ordering = ['-start_time']
        constraints = [
            models.UniqueConstraint(fields=['market_code'], name='unique_market_code_status')
        ]

    def __str__(self):
        return f"{self.market_code.code} maintenance from {self.start_time} to {self.end_time}"

    @property
    def server_check(self):
        now = timezone.now()
        # Safely handle if end_time or start_time are None, return False in that case
        if self.start_time is not None and self.end_time is not None:
            return self.start_time <= now <= self.end_time
        return False