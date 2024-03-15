import re

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import SELECT_CLASSES

from lib.status import HTTP_204_NO_CONTENT
from tradecore.models import (
    EnabledMarketCodeCombination,
    Node,
    TradeConfigAllocation,
)
from tradecore.views import TradeConfigViewSet


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
        "node",
        "target_market_code",
        "origin_market_code",
        "user",
        "trade_config_uuid",
        "delete_button",
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

    def delete_button(self, obj):
        delete_button_class = (
            "block border border-red-500 font-medium px-3 py-2 rounded-md text-center text-sm "
            "text-red-500 whitespace-nowrap dark:border-transparent dark:bg-red-500/20 dark:text-red-500"
        )
        return mark_safe(
            f'<a class="{delete_button_class}" href="/admin/tradecore/tradeconfigallocation/{obj.id}/delete/">'
            "Delete"
            "</a>"
        )

    delete_button.short_description = "Delete?"

    def get_actions(self, request):
        """
        We need to allow has_delete_permissions to be able to delete a TradeConfigAllocation, but at the same time,
        remove bulk delete since we have to call trade_core api for each object we want to delete.
        """
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        api_response = TradeConfigViewSet().tradecore_destroy_api(
            url=obj.node.url,
            endpoint=TradeConfigViewSet.tradecore_api_endpoint,
            path_param=obj.trade_config_uuid,
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            return super().delete_model(request, obj)

        try:
            message = api_response.json()
            message = message["detail"] if "detail" in message else message
        except Exception:
            message = api_response.content

        self.message_user(request, message, messages.ERROR)

    def response_delete(self, request, obj_display, obj_id):
        try:
            TradeConfigAllocation.objects.get(id=obj_id)
            url = reverse(
                "admin:%s_%s_changelist" % (self.opts.app_label, self.opts.model_name),
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(url)

        except TradeConfigAllocation.DoesNotExist:
            return super().response_delete(request, obj_display, obj_id)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(EnabledMarketCodeCombination, EnabledMarketCodeCombinationAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(TradeConfigAllocation, TradeConfigAllocationAdmin)
