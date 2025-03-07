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

# Add this Trade model
class Trade(models.Model):
    """
    Proxy model for trades from the external API.
    Does not create a database table.
    """
    uuid = models.UUIDField(primary_key=True)
    trade_config_uuid = models.UUIDField(
        help_text="Trade config uuid related to user",
        verbose_name="Trade Config UUID",
    )
    registered_datetime = models.DateTimeField(null=True, blank=True)
    base_asset = models.CharField(max_length=50)
    usdt_conversion = models.BooleanField(null=True, blank=True)
    low = models.DecimalField(max_digits=8, decimal_places=3)
    high = models.DecimalField(max_digits=8, decimal_places=3)
    trigger_switch = models.IntegerField(null=True, blank=True)
    trade_switch = models.IntegerField(null=True, blank=True)
    trade_capital = models.IntegerField(null=True, blank=True)
    last_trade_history_uuid = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Trade {self.uuid}"
    
    class Meta:
        managed = False  # No database table creation
        verbose_name = "Trade"
        verbose_name_plural = "Trades"

class TradeLog(models.Model):
    """
    Proxy model for trade logs from the external API.
    Does not create a database table.
    """
    uuid = models.UUIDField(primary_key=True)
    trade_uuid = models.UUIDField()
    trade_config_uuid = models.UUIDField(
        help_text="Trade config uuid related to user",
        verbose_name="Trade Config UUID",
    )
    registered_datetime = models.DateTimeField(null=True, blank=True)
    base_asset = models.CharField(max_length=50)
    usdt_conversion = models.BooleanField(null=True, blank=True)
    low = models.DecimalField(max_digits=8, decimal_places=3)
    high = models.DecimalField(max_digits=8, decimal_places=3)
    trade_capital = models.IntegerField(null=True, blank=True)
    deleted = models.BooleanField(default=False)
    status = models.CharField(max_length=100, null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"TradeLog {self.uuid}"
    
    class Meta:
        managed = False  # No database table creation
        verbose_name = "Trade Log"
        verbose_name_plural = "Trade Logs"

class OrderHistory(models.Model):
    """
    Proxy model for order history from the external API.
    Does not create a database table.
    """
    id = models.IntegerField(primary_key=True)
    order_id = models.CharField(max_length=100)
    trade_config_uuid = models.UUIDField(
        help_text="Trade config uuid related to user",
        verbose_name="Trade Config UUID",
    )
    trade_uuid = models.UUIDField(null=True, blank=True)
    registered_datetime = models.DateTimeField(null=True, blank=True)
    order_type = models.CharField(max_length=50)
    market_code = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    quote_asset = models.CharField(max_length=20)
    side = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=21, decimal_places=11)
    qty = models.DecimalField(max_digits=22, decimal_places=9)
    fee = models.DecimalField(max_digits=15, decimal_places=9)
    remark = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.order_id}"
    
    class Meta:
        managed = False  # No database table creation
        verbose_name = "Order History"
        verbose_name_plural = "Order History"

class TradeHistory(models.Model):
    """
    Proxy model for trade history from the external API.
    Does not create a database table.
    """
    uuid = models.UUIDField(primary_key=True)
    trade_config_uuid = models.UUIDField(
        help_text="Trade config uuid related to user",
        verbose_name="Trade Config UUID",
    )
    trade_uuid = models.UUIDField(null=True, blank=True)
    registered_datetime = models.DateTimeField(null=True, blank=True)
    trade_side = models.CharField(max_length=50)
    base_asset = models.CharField(max_length=50)
    target_order_id = models.CharField(max_length=100)
    origin_order_id = models.CharField(max_length=100)
    target_premium_value = models.DecimalField(max_digits=8, decimal_places=3)
    executed_premium_value = models.DecimalField(max_digits=8, decimal_places=3)
    slippage_p = models.DecimalField(max_digits=6, decimal_places=3)
    dollar = models.DecimalField(max_digits=5, decimal_places=1)
    remark = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Trade History {self.uuid}"
    
    class Meta:
        managed = False  # No database table creation
        verbose_name = "Trade History"
        verbose_name_plural = "Trade History"

class RepeatTrade(models.Model):
    """
    Proxy model for repeat trades from the external API.
    Does not create a database table.
    """
    uuid = models.UUIDField(primary_key=True)
    trade_uuid = models.UUIDField()
    registered_datetime = models.DateTimeField(null=True, blank=True)
    last_updated_datetime = models.DateTimeField(null=True, blank=True)
    kline_interval = models.CharField(max_length=50)
    kline_num = models.IntegerField(null=True, blank=True)
    pauto_num = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    auto_repeat_switch = models.SmallIntegerField(null=True, blank=True)
    auto_repeat_num = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"RepeatTrade {self.uuid}"
    
    class Meta:
        managed = False  # No database table creation
        verbose_name = "Repeat Trade"
        verbose_name_plural = "Repeat Trades"
