from django.forms import model_to_dict
from rest_framework import exceptions, serializers

from messagecore.models import Message
from users.models import User


class MessageSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        try:
            user = User.objects.get(telegram_chat_id=attrs["telegram_chat_id"])
        except User.DoesNotExist:
            raise exceptions.ValidationError(
                {
                    "telegram_chat_id": [
                        f"User with telegram_chat_id {attrs['telegram_chat_id']} does not exist!"
                    ]
                }
            )
        except User.MultipleObjectsReturned:
            raise exceptions.ValidationError(
                {
                    "telegram_chat_id": [
                        "This telegram_chat_id is linked to multiple users!"
                    ]
                }
            )

        user_telegram_socialapps = user.socialapps.filter(
            socialapp__provider="telegram"
        )

        if user_telegram_socialapps.first():
            telegram_bot = user_telegram_socialapps.first().socialapp
            attrs["telegram_bot_username"] = telegram_bot.client_id
        else:
            raise exceptions.ValidationError(
                {
                    "telegram_chat_id": [
                        f"User with telegram_chat_id {attrs['telegram_chat_id']} has no associated Telegram Bot!"
                    ]
                }
            )

        return super().validate(attrs)

    def update(self, instance, validated_data):
        allowed_update_fields = ["read"]

        new_validated_data = model_to_dict(instance)
        for key, value in validated_data.items():
            if key in allowed_update_fields and value != getattr(instance, key):
                new_validated_data[key] = value

        return super().update(instance, new_validated_data)

    class Meta:
        model = Message
        fields = "__all__"
        extra_kwargs = {
            "telegram_bot_username": {"read_only": True},
        }
