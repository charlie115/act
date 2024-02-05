from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin, TabularInline

from tradecore.models import (
    Node,
    NodeMarketCodeService,
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


class NodeMarketCodeServiceInline(TabularInline):
    model = NodeMarketCodeService
    extra = 0
    verbose_name = "Market Code Service"

    def has_change_permission(self, request, obj=None):
        return False


class NodeAdmin(ModelAdmin):
    fields = ["name", "url", "description", "max_user_count"]
    list_display = ["name", "url", "description", "get_market_code_services"]
    search_fields = ["name", "url"]
    inlines = (
        NodeMarketCodeServiceInline,
        UsersInline,
    )

    def get_market_code_services(self, obj):
        return mark_safe(
            "<br>".join(
                [
                    f"{market_code_service.target.code}:{market_code_service.origin.code}"
                    for market_code_service in obj.market_code_services.all()
                ]
            )
        )

    get_market_code_services.short_description = "Market Code Services"
    get_market_code_services.allow_tags = True


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


admin.site.register(Node, NodeAdmin)
admin.site.register(TradeConfigAllocation, TradeConfigAllocationAdmin)
