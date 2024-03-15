from django.core.validators import URLValidator
from django.db import models

from infocore.models import MarketCode
from users.models import User


class EnabledMarketCodeCombination(models.Model):
    target = models.ForeignKey(
        MarketCode,
        on_delete=models.CASCADE,
        related_name="target",
    )
    origin = models.ForeignKey(
        MarketCode,
        on_delete=models.CASCADE,
        related_name="origin",
    )
    trade_support = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.target}:{self.origin} Trade={self.trade_support}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["target", "origin"],
                name="unique__target__origin",
            )
        ]
        verbose_name = "Enabled Market Code Combination"


class Node(models.Model):
    name = models.CharField(max_length=150)
    url = models.CharField(
        max_length=200,
        verbose_name="URL",
        validators=[URLValidator()],
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    max_user_count = models.IntegerField(default=300)
    users = models.ManyToManyField(User, related_name="nodes")
    market_code_combinations = models.ManyToManyField(
        EnabledMarketCodeCombination, blank=True
    )

    def __str__(self):
        return self.name


class TradeConfigAllocation(models.Model):
    node = models.ForeignKey(
        Node, on_delete=models.DO_NOTHING, related_name="trade_config_allocations"
    )
    target_market_code = models.CharField(
        max_length=150,
        verbose_name="Target Market Code",
    )
    origin_market_code = models.CharField(
        max_length=150,
        verbose_name="Origin Market Code",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="trade_config_allocations",
    )
    trade_config_uuid = models.UUIDField(
        help_text="Trade config uuid from trade_core",
        verbose_name="Trade Config UUID",
    )

    def __str__(self):
        return f"({self.node}) Trade Config {self.trade_config_uuid}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_market_code", "origin_market_code"],
                name="unique__user__target__origin",
            )
        ]
        verbose_name = "Trade Config Allocation"
