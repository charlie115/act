from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from unfold.admin import ModelAdmin

from infocore.mixins import AssetMixin
from infocore.models import Asset, MarketCode


class AssetAdmin(AssetMixin, ModelAdmin):
    list_display = [
        "symbol",
        "get_icon_preview",
        "note",
        "last_update",
    ]
    search_fields = ["symbol"]
    readonly_fields = ["symbol", "last_update"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "symbol",
                    "icon",
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


class MarketCodeAdmin(ModelAdmin):
    list_display = [
        "name",
        "code",
    ]
    search_fields = ["code", "name"]
    ordering = ["name"]


admin.site.register(Asset, AssetAdmin)
admin.site.register(MarketCode, MarketCodeAdmin)
