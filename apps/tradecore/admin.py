from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin, TabularInline

from tradecore.models import (
    EnabledMarketCodeCombination,
    Node,
    TradeConfigAllocation,
)


class UsersInline(TabularInline):
    model = Node.users.through
    verbose_name = "User"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class EnabledMarketCodeCombinationAdmin(ModelAdmin):
    list_display = [
        "target",
        "origin",
        "trade_support",
    ]
    list_filter = [
        "target",
        "origin",
        "trade_support",
    ]
    search_fields = [
        "target",
        "origin",
        "trade_support",
    ]


class NodeAdmin(ModelAdmin):
    fields = [
        "name",
        "url",
        "description",
        "max_user_count",
        "market_code_combinations",
    ]
    list_display = ["name", "url", "description", "get_market_code_combinations"]
    search_fields = ["name", "url"]
    autocomplete_fields = ["market_code_combinations"]
    inlines = [
        UsersInline,
    ]

    def get_market_code_combinations(self, obj):
        bg_color = {True: "green", False: "red"}
        trade_class = "px-2 py-1 rounded text-xxs bg-{bg_color}-100 text-{bg_color}-500 dark:bg-{bg_color}-500/20"

        return mark_safe(
            "".join(
                [
                    f"<p class='my-2'>{market_code_combo.target.code}:{market_code_combo.origin.code}&nbsp;&nbsp;"
                    f"<small class='{trade_class.format(bg_color=bg_color[market_code_combo.trade_support])}'>"
                    "Trade Support</small></p>"
                    for market_code_combo in obj.market_code_combinations.all()
                ]
            )
        )

    get_market_code_combinations.short_description = "Market Code Combinations"
    get_market_code_combinations.allow_tags = True


class TradeConfigAllocationAdmin(ModelAdmin):
    list_display = [
        "node_link",
        "target_market_code",
        "origin_market_code",
        "user_link",
        "trade_config_uuid",
    ]
    search_fields = [
        "node__name",
        "node__url",
        "target_market_code",
        "origin_market_code",
        "user__uuid",
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
        "trade_config_uuid",
    ]

    def node_link(self, obj):
        url = reverse("admin:tradecore_node_change", args=(obj.node.id,))
        return mark_safe(f"<a href='{url}'>{obj.node}</a>")

    node_link.short_description = "Node"

    def user_link(self, obj):
        url = reverse("admin:users_user_change", args=(obj.user.id,))
        return mark_safe(f"<a href='{url}'>{obj.user}</a>")

    user_link.short_description = "User"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(EnabledMarketCodeCombination, EnabledMarketCodeCombinationAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(TradeConfigAllocation, TradeConfigAllocationAdmin)
