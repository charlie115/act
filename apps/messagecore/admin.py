from django.contrib import admin

from unfold.admin import ModelAdmin

from messagecore.models import Message


class MessageAdmin(ModelAdmin):
    list_display = [
        "title",
        "datetime",
        "telegram_bot_name",
        "telegram_chat_id",
        "origin",
        "type",
        "code",
        "sent",
        "send_count",
    ]
    list_filter = [
        "telegram_bot_name",
        "origin",
        "type",
        "code",
        "sent",
    ]
    search_fields = [
        "title",
        "datetime",
        "telegram_bot_name",
        "telegram_chat_id",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Message, MessageAdmin)
