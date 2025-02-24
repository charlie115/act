from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.widgets import INPUT_CLASSES, SELECT_CLASSES

from messagecore.models import Message
from socialaccounts.models import SocialApp
from users.models import User


class TelegramChatIdChoiceField(forms.ModelChoiceField):
    widget = forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])})
    help_text = "Only users that have connected their telegram account are allowed to create messages."

    def label_from_instance(self, obj):
        return f"{obj.telegram_chat_id} ({obj.email})"


class MessageForm(forms.ModelForm):
    telegram_bot_username = forms.ModelChoiceField(
        required=True,
        queryset=SocialApp.objects.values_list("client_id", flat=True),
        blank=False,
        to_field_name="client_id",
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )
    telegram_chat_id = TelegramChatIdChoiceField(
        required=True,
        queryset=User.objects.exclude(
            telegram_chat_id__isnull=True,
        ).exclude(
            telegram_chat_id__exact="",
        ),
        blank=False,
        to_field_name="telegram_chat_id",
    )
    content = forms.CharField(
        widget=forms.Textarea({"class": " ".join([*INPUT_CLASSES])}),
    )
    origin = forms.CharField(
        initial="acw_django_admin",
        widget=forms.TextInput({"class": " ".join([*INPUT_CLASSES])}),
    )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("telegram_chat_id"):
            cleaned_data["telegram_chat_id"] = cleaned_data[
                "telegram_chat_id"
            ].telegram_chat_id

        if "telegram_bot_username" not in cleaned_data:
            raise forms.ValidationError("telegram_bot_username")

        if "telegram_chat_id" not in cleaned_data:
            raise forms.ValidationError("telegram_chat_id")

        user = User.objects.get(telegram_chat_id=cleaned_data.get("telegram_chat_id"))
        user_telegram_bots = list(
            user.socialapps.values_list("socialapp__client_id", flat=True)
        )

        if cleaned_data["telegram_bot_username"] not in user_telegram_bots:
            raise forms.ValidationError(
                {"telegram_bot_username": "User is not linked to this telegram bot."}
            )

        return cleaned_data

    class Meta:
        model = Message
        fields = "__all__"


class MessageAdmin(ModelAdmin):
    list_display = [
        "title",
        "datetime",
        "display_telegram_bot",
        "display_telegram_chat_id",
        "origin",
        "type",
        # "code",
        "sent",
        "send_times",
        "send_term",
        "read",
    ]
    list_filter = [
        "telegram_bot_username",
        "origin",
        "type",
        "code",
        "sent",
        "read",
    ]
    search_fields = [
        "title",
        "datetime",
        "telegram_bot_username",
        "telegram_chat_id",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "datetime",
                    ("telegram_bot_username", "telegram_chat_id"),
                    "title",
                    "content",
                    "remarks",
                    ("origin", "type"),
                    "code",
                    "sent",
                    ("send_times", "send_term"),
                    "read",
                )
            },
        ),
    )
    form = MessageForm

    @display(description=_("Telegram bot"))
    def display_telegram_bot(self, instance):
        return instance.telegram_bot_username

    @display(description=_("Telegram ID"))
    def display_telegram_chat_id(self, instance):
        return instance.telegram_chat_id

    def has_change_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Message, MessageAdmin)
