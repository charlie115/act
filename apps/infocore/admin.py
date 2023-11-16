from django.apps import apps
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django_rq.admin import QueueAdmin
from django_rq.models import Queue
from unfold.admin import ModelAdmin

from infocore.mixins import AssetMixin
from infocore.models import Asset


class CustomQueueAdmin(QueueAdmin, ModelAdmin):
    pass


class AssetAdmin(AssetMixin, ModelAdmin):
    list_display = [
        "symbol",
        "get_icon_preview",
        "note",
        "last_update",
    ]
    search_fields = ["symbol"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "symbol",
                    "get_icon",
                    "note",
                    "last_update",
                )
            },
        ),
    )
    ordering = ("symbol",)
    actions = ["pull_new_icon_image"]

    def pull_new_icon_image(self, request, queryset):
        for obj in queryset:
            info = self.pull_asset_info(obj.symbol)
            icon = self.get_icon_image(info)

            obj.icon = icon
            obj.last_update = now()
            obj.save()

    pull_new_icon_image.short_description = "Pull new icon image"
    pull_new_icon_image.allow_tags = True

    def get_icon_preview(self, obj):
        return self.get_icon(obj, width="width=40rem", height="height=40rem")

    get_icon_preview.allow_tags = True
    get_icon_preview.short_description = "Icon"

    def get_icon(self, obj, width="", height=""):
        if obj.icon and hasattr(obj.icon, "url"):
            icon_html = (
                f'<a href="{obj.icon.url}">'
                f'<img src="{obj.icon.url}" {width} {height}/>'
                "</a>"
            )
            return mark_safe(icon_html)

    get_icon.allow_tags = True
    get_icon.short_description = "Icon"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Queue)

admin.site.register(Asset, AssetAdmin)
admin.site.register(Queue, CustomQueueAdmin)

apps.get_app_config("django_rq").verbose_name = "Redis Queue"
