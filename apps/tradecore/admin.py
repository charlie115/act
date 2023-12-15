from django import forms
from django.contrib import admin

from unfold.admin import ModelAdmin

from tradecore.mixins import NodeValidatorMixin
from tradecore.models import Node, UserConfig


class NodeForm(NodeValidatorMixin, forms.ModelForm):
    pass


class NodeAdmin(ModelAdmin):
    list_display = [
        "name",
        "domain",
        "port",
        "description",
    ]
    search_fields = ["name", "domain"]
    form = NodeForm


class UserConfigAdmin(ModelAdmin):
    list_display = [
        "user",
        "node",
        "service_expiry_date",
    ]
    search_fields = [
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
        "node__name",
        "node__domain",
    ]


admin.site.register(Node, NodeAdmin)
admin.site.register(UserConfig, UserConfigAdmin)
