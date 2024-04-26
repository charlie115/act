from django.db.models import Count
from rest_framework import serializers

from lib.datetime import DATE_TIME_FORMAT
from tradecore.serializers import TradeConfigAllocationSerializer
from users.mixins import UserFavoriteAssetsValidatorMixin, UserUUIDSerializerMixin
from users.models import (
    User,
    UserBlocklist,
    UserFavoriteAssets,
    UserProfile,
    UserSocialApps,
    DepositBalance,
    DepositHistory,
)
from socialaccounts.models import ProxySocialApp
from socialaccounts.serializers import ProxySocialAppSerializer


class UserOwnedSerializer(UserUUIDSerializerMixin, serializers.ModelSerializer):
    def validate(self, attrs):
        attrs["user"] = self.context["request"].user
        return super().validate(attrs)


class UserFavoriteAssetsSerializer(
    UserFavoriteAssetsValidatorMixin,
    UserOwnedSerializer,
):
    class Meta:
        model = UserFavoriteAssets
        fields = ("id", "base_asset", "market_codes")


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
        fields = ("level", "points", "picture")


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    favorite_assets = UserFavoriteAssetsSerializer(many=True, read_only=True)
    socialapps = serializers.SerializerMethodField()
    trade_config_allocations = TradeConfigAllocationSerializer(
        many=True, read_only=True
    )

    def get_socialapps(self, instance):
        socialapps = [
            ProxySocialAppSerializer(socialapps.socialapp).data
            for socialapps in instance.socialapps.all()
        ]
        return socialapps

    def _get_telegram_bots(self):
        """Get social apps with telegram provider

        Returns:
            Telegram bots starting from the least number of users allocated
        """

        telegram_socialapps = (
            ProxySocialApp.objects.filter(provider="telegram")
            .annotate(user_count=Count("users"))
            .order_by("user_count", "id")
        )

        return telegram_socialapps

    def create(self, validated_data):
        validated_data.pop("username", None)
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Telegram authentication (unlike node, socialapps don't need to be validated)
        telegram_socialapps = self._get_telegram_bots()
        if len(telegram_socialapps) > 0:
            UserSocialApps.objects.create(
                socialapp=telegram_socialapps.first(),
                user=user,
            )

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
            "date_joined",
            "profile",
            "favorite_assets",
            "socialapps",
            "telegram_chat_id",
            "trade_config_allocations",
        )
        read_only_fields = ("role", "is_active")
        extra_kwargs = {
            "email": {"style": {"input_type": "email", "placeholder": "Email"}},
            "password": {
                "write_only": True,
                "style": {"input_type": "password", "placeholder": "Password"},
            },
            "date_joined": {"read_only": True},
            "telegram_chat_id": {"read_only": True},
        }


class UserBlocklistSerializer(serializers.ModelSerializer):
    datetime = serializers.DateTimeField(required=False, format=DATE_TIME_FORMAT)

    class Meta:
        model = UserBlocklist
        fields = ("id", "target_username", "target_ip", "datetime")


class DepositBalanceSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field="uuid")

    class Meta:
        model = DepositBalance
        fields = ("id", "user", "balance", "last_update")
        extra_kwargs = {
            "last_update": {"read_only": True},
        }


class DepositHistorySerializer(UserUUIDSerializerMixin, serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field="uuid")
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DepositHistory
        fields = (
            "user",
            "balance",
            "change",
            "txid",
            "type",
            "pending",
            "registered_datetime",
        )
