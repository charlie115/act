from django.core.validators import URLValidator
from django.db import models

from infocore.models import MarketCode
from users.models import User


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

    def __str__(self):
        return self.name


class NodeMarketCodeService(models.Model):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="market_code_services"
    )
    target = models.ForeignKey(
        MarketCode,
        on_delete=models.DO_NOTHING,
        related_name="target",
    )
    origin = models.ForeignKey(
        MarketCode,
        on_delete=models.DO_NOTHING,
        related_name="origin",
    )

    def __str__(self):
        return f"[{self.node}] {self.target}:{self.origin}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["node", "target", "origin"],
                name="unique__node__target__origin",
            )
        ]
        verbose_name = "Node MarketCode Service"


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_market_code", "origin_market_code"],
                name="unique__user__target__origin",
            )
        ]
        verbose_name = "Trade Config Allocation"
