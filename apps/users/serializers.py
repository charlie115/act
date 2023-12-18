from django.db.models import Count
from rest_framework import exceptions, serializers

from lib.datetime import DATE_TIME_FORMAT
from users.mixins import UserFavoriteAssetsValidatorMixin, UserUUIDSerializerMixin
from users.models import User, UserBlocklist, UserFavoriteAssets, UserProfile
from tradecore.models import Node
from tradecore.serializers import UserConfigSerializer


class UserFavoriteAssetsSerializer(
    UserUUIDSerializerMixin,
    UserFavoriteAssetsValidatorMixin,
    serializers.ModelSerializer,
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
        fields = ("referral", "level", "points", "picture")


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    favorite_assets = UserFavoriteAssetsSerializer(many=True, read_only=True)
    trade_config = UserConfigSerializer(read_only=True)

    def validate(self, attrs):
        nodes = (
            Node.objects.all()
            .annotate(user_count=Count("users"))
            .order_by("user_count", "id")
        )

        if len(nodes) > 0:
            attrs["node"] = nodes.first()
        else:
            raise exceptions.ValidationError(
                {"detail": "There is no Node to assign user!"}
            )

        return super().validate(attrs)

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
            "date_joined",
            "profile",
            "favorite_assets",
            "node",
            "trade_config",
        )
        read_only_fields = ("role", "is_active")
        extra_kwargs = {
            "email": {"style": {"input_type": "email", "placeholder": "Email"}},
            "password": {
                "write_only": True,
                "style": {"input_type": "password", "placeholder": "Password"},
            },
            "date_joined": {"read_only": True},
            "node": {"read_only": True},
        }


class UserBlocklistSerializer(serializers.ModelSerializer):
    datetime = serializers.DateTimeField(required=False, format=DATE_TIME_FORMAT)

    class Meta:
        model = UserBlocklist
        fields = ("id", "target_username", "target_ip", "datetime")
