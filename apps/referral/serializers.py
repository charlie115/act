from rest_framework import serializers

from referral.mixins import ReferralCodeMixin
from referral.models import Referral, ReferralCode, ReferralGroup
from users.models import User


class ReferralSerializer(serializers.ModelSerializer):
    referred_user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field="uuid"
    )
    referral_code = serializers.SlugRelatedField(
        queryset=ReferralCode.objects.all(), slug_field="code"
    )

    class Meta:
        model = Referral
        fields = "__all__"


class ReferralGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralGroup
        exclude = ["id", "description"]


class ReferralCodeSerializer(ReferralCodeMixin, serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field="uuid")
    referral_group = ReferralGroupSerializer()

    class Meta:
        model = ReferralCode
        fields = (
            "id",
            "user",
            "code",
            "target_market_code",
            "origin_market_code",
            "max_depth",
            "contact",
            "referral_group",
        )  # explicitly stated instead of __all__ for ordering
