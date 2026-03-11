from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group as BaseGroup

from rest_framework.authtoken.models import TokenProxy as DRFToken
from unfold.admin import ModelAdmin

from authentication.models import ProxyGroup, ProxyToken


class ProxyGroupAdmin(BaseGroupAdmin, ModelAdmin):
    class Meta:
        model = ProxyGroup
        verbose_name = "Group"


class ProxyTokenAdmin(ModelAdmin):
    search_fields = [
        "user__email",
        "user__username",
        "key",
    ]

    # def has_add_permission(self, request, obj=None):
    #     return False

    class Meta:
        model = ProxyToken


admin.site.unregister(DRFToken)
admin.site.unregister(BaseGroup)
admin.site.register(ProxyToken, ProxyTokenAdmin)
admin.site.register(ProxyGroup, ProxyGroupAdmin)
