import re

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import SELECT_CLASSES

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


class EnabledMarketCodeCombinationForm(forms.ModelForm):
    target = forms.ChoiceField(
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )
    origin = forms.ChoiceField(
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )

    class Meta:
        model = EnabledMarketCodeCombination
        fields = "__all__"


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

    def changelist_view(self, request, *args, **kwargs):
        self.request = request
        return super().changelist_view(request, *args, **kwargs)

    def get_market_code_combinations(self, obj):
        mobile_agent_regex = re.compile(
            r".*(iphone|mobile|androidtouch)", re.IGNORECASE
        )

        bg_color = {True: "green", False: "red"}
        trade_class = "px-2 py-1 rounded text-xxs bg-{bg_color}-100 text-{bg_color}-500 dark:bg-{bg_color}-500/20"

        new_line = ""
        market_code_combinations = []

        for market_code_combo in obj.market_code_combinations.all():
            if mobile_agent_regex.match(self.request.META["HTTP_USER_AGENT"]):
                new_line = "<br>"
                market_code_combinations.append(
                    f"{market_code_combo.target.code}:{market_code_combo.origin.code}<br>"
                    f"Trade Support={market_code_combo.trade_support}<br>"
                )
            else:
                market_code_combinations.append(
                    f"<p class='my-2'>{market_code_combo.target.code}:{market_code_combo.origin.code}&nbsp;&nbsp;"
                    f"<small class='{trade_class.format(bg_color=bg_color[market_code_combo.trade_support])}'>"
                    "Trade Support</small></p>"
                )

        return mark_safe(new_line.join(market_code_combinations))

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
