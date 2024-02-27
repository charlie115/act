from django import forms
from django.contrib import admin

from unfold.admin import ModelAdmin
from unfold.widgets import INPUT_CLASSES, SELECT_CLASSES

from messagecore.models import Message
from socialaccounts.models import SocialApp
from users.models import User


class MessageForm(forms.ModelForm):
    telegram_bot_username = forms.ChoiceField(
        choices=[(bot.client_id, bot.name) for bot in SocialApp.objects.all()],
        required=True,
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )
    telegram_chat_id = forms.ChoiceField(
        choices=[
            (user.telegram_chat_id, f"{user.telegram_chat_id} ({user.email})")
            for user in User.objects.all()
        ],
        required=True,
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
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
        "telegram_bot_username",
        "telegram_chat_id",
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
    form = MessageForm

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Message, MessageAdmin)
