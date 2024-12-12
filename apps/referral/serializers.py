from rest_framework import serializers
from .models import AffiliateTier, Affiliate, ReferralCode, Referral
from users.models import User
from decimal import Decimal

class AffiliateTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateTier
        fields = [
            'id',
            'name',
            'base_commission_rate',
            'parent_commission_rate',
            'required_total_commission',
        ]
        read_only_fields = ['id']


class AffiliateSerializer(serializers.ModelSerializer):
    # Display parent affiliate and tier as ids
    parent_affiliate = serializers.PrimaryKeyRelatedField(
        queryset=Affiliate.objects.all(),
        required=False,
        allow_null=True
    )
    tier = serializers.PrimaryKeyRelatedField(queryset=AffiliateTier.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Affiliate
        fields = [
            'id',
            'user',
            'parent_affiliate',
            'affiliate_code',
            'tier',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReferralCodeSerializer(serializers.ModelSerializer):
    affiliate = serializers.PrimaryKeyRelatedField(queryset=Affiliate.objects.all())

    # The clean() method in the model ensures that user_discount_rate + self_commission_rate = 1
    # We will only allow user to set user_discount_rate and automatically computed inside model
    # If you want to show user the computed self_commission_rate, we can make it read-only.
    self_commission_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4, read_only=True
    )

    class Meta:
        model = ReferralCode
        fields = [
            'id',
            'affiliate',
            'code',
            'user_discount_rate',
            'self_commission_rate',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'self_commission_rate']


class ReferralSerializer(serializers.ModelSerializer):
    referral_code = serializers.PrimaryKeyRelatedField(queryset=ReferralCode.objects.all())
    referred_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Referral
        fields = [
            'id',
            'referred_user',
            'referral_code',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReferralCommissionQueryParamsSerializer(serializers.Serializer):
    """
    Serializer to validate query parameters for commission calculation.
    Adjust fields as needed based on your actual query parameters.
    """
    user = serializers.UUIDField(required=True)
    initial_profit = serializers.DecimalField(max_digits=20, decimal_places=8, required=True)
    apply_to_deposit = serializers.BooleanField(default=False)
    trade_uuid = serializers.UUIDField(required=False)