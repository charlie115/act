from rest_framework import serializers

from arbot.serializers import ArbotUserConfigSerializer
from users.mixins import UserUUIDSerializerMixin
from users.models import User, UserFavoriteSymbols, UserProfile


class UserFavoriteSymbolsSerializer(
    UserUUIDSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = UserFavoriteSymbols
        fields = ("user", "market_name_1", "market_name_2", "base_symbol")
        extra_kwargs = {
            "user": {"write_only": True},
        }


class UserProfileSerializer(UserUUIDSerializerMixin, serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    def get_picture(self, obj):
        google_accounts = obj.user.socialaccount_set.filter(provider="google")
        if len(google_accounts) > 0:
            return google_accounts.first().extra_data["picture"]
        else:
            return None

    class Meta:
        model = UserProfile
        fields = ("referral", "level", "points", "picture")


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    favorite_symbols = UserFavoriteSymbolsSerializer(many=True, read_only=True)
    arbot_config = ArbotUserConfigSerializer(read_only=True)

    def create(self, validated_data):
        validated_data.pop("username", None)
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

    class Meta:
        model = User
        fields = (
            "uuid",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "profile",
            "favorite_symbols",
            "arbot_config",
        )
        read_only_fields = ("role", "is_active")
        extra_kwargs = {
            "email": {"style": {"input_type": "email", "placeholder": "Email"}},
            "password": {
                "write_only": True,
                "style": {"input_type": "password", "placeholder": "Password"},
            },
        }
