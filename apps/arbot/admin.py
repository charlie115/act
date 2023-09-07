from django import forms
from django.contrib import admin

from unfold.admin import ModelAdmin

from arbot.mixins import ArbotNodeValidatorMixin
from arbot.models import ArbotNode, ArbotUserConfig


class ArbotNodeForm(ArbotNodeValidatorMixin, forms.ModelForm):
    pass


class ArbotNodeAdmin(ModelAdmin):
    list_display = [
        "name",
        "domain",
        "port",
        "description",
    ]
    search_fields = ["name", "domain"]
    form = ArbotNodeForm


class ArbotUserConfigAdmin(ModelAdmin):
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


admin.site.register(ArbotNode, ArbotNodeAdmin)
admin.site.register(ArbotUserConfig, ArbotUserConfigAdmin)
