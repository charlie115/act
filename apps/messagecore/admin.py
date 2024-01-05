from django.contrib import admin

from unfold.admin import ModelAdmin

from messagecore.models import Message


class MessageAdmin(ModelAdmin):
    list_display = [
        "title",
        "datetime",
        "telegram_bot_username",
        "telegram_chat_id",
        "origin",
        "type",
        "code",
        "sent",
        "send_times",
        "send_term",
    ]
    list_filter = [
        "telegram_bot_username",
        "origin",
        "type",
        "code",
        "sent",
    ]
    search_fields = [
        "title",
        "datetime",
        "telegram_bot_username",
        "telegram_chat_id",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Message, MessageAdmin)
