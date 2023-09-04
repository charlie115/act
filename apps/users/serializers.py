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
    class Meta:
        model = UserProfile
        fields = ("referral", "level", "points")


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source="userprofile", read_only=True)
    favorite_symbols = UserFavoriteSymbolsSerializer(many=True, read_only=True)
    arbot_config = ArbotUserConfigSerializer()

    def create(self, validated_data):
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
            "password",
            "first_name",
            "last_name",
            "is_active",
            "profile",
            "favorite_symbols",
            "arbot_config",
        )
        extra_kwargs = {
            "email": {"style": {"input_type": "email", "placeholder": "Email"}},
            "password": {
                "write_only": True,
                "style": {"input_type": "password", "placeholder": "Password"},
            },
            "is_active": {"read_only": True},
        }
