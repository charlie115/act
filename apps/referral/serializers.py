from rest_framework import serializers
from .models import AffiliateTier, Affiliate, ReferralCode, Referral, AffiliateRequest, CommissionHistory, CommissionBalance
from users.models import User
from decimal import Decimal
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum

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
    user = serializers.UUIDField(source='user.uuid', read_only=True)
    referral_count = serializers.SerializerMethodField()
    total_earned_commission = serializers.SerializerMethodField()
    total_forwarded_commission = serializers.SerializerMethodField()
    total_direct_commission = serializers.SerializerMethodField()

    class Meta:
        model = Affiliate
        fields = [
            'id',
            'user',
            'parent_affiliate',
            'affiliate_code',
            'tier',
            'created_at',
            'referral_count',
            'total_earned_commission',
            'total_direct_commission',
            'total_forwarded_commission',
        ]
        read_only_fields = ['created_at', 'id']
        
    def get_referral_count(self, instance):
        # Count how many referrals have used any of this affiliate's referral codes
        # Since ReferralCode -> affiliate is a FK, we can filter Referral by referral_code__affiliate=instance
        count = Referral.objects.filter(referral_code__affiliate=instance).count()
        return count
        
    def get_total_earned_commission(self, instance):
        # Sum all COMMISSION type changes for this affiliate
        total = CommissionHistory.objects.filter(
            affiliate=instance,
            type=CommissionHistory.COMMISSION
        ).aggregate(total=Sum('change'))['total']
        
        if total is None:
            total = Decimal('0.00')
        return total
    
    def get_total_direct_commission(self, instance):
        # Direct commissions: no child_affiliate involved
        total = CommissionHistory.objects.filter(
            affiliate=instance,
            type=CommissionHistory.COMMISSION,
            child_affiliate__isnull=True
        ).aggregate(total=Sum('change'))['total'] or Decimal('0.00')
        return total

    def get_total_forwarded_commission(self, instance):
        # Forwarded commissions: earned from sub-affiliates (child_affiliate is not null)
        total = CommissionHistory.objects.filter(
            affiliate=instance,
            type=CommissionHistory.COMMISSION,
            child_affiliate__isnull=False
        ).aggregate(total=Sum('change'))['total'] or Decimal('0.00')
        return total

class SubAffiliateSerializer(serializers.ModelSerializer):
    # Only the fields you want for sub-affiliates
    user = serializers.CharField(source='user.username', read_only=True)
    parent_affiliate = serializers.PrimaryKeyRelatedField(read_only=True)
    tier = serializers.CharField(source='tier.name', read_only=True)
    referral_count = serializers.SerializerMethodField()
    total_earned_commission = serializers.SerializerMethodField()
    total_forwarding_commission = serializers.SerializerMethodField()

    class Meta:
        model = Affiliate
        fields = [
                'id',
                'user',
                'parent_affiliate',
                'tier',
                'created_at',
                'referral_count',
                'total_earned_commission',
                'total_forwarding_commission',
            ]
        read_only_fields = ['id', 'created_at']
        
    def get_referral_count(self, instance):
        # Count how many referrals have used any of this affiliate's referral codes
        # Since ReferralCode -> affiliate is a FK, we can filter Referral by referral_code__affiliate=instance
        count = Referral.objects.filter(referral_code__affiliate=instance).count()
        return count
    
    def get_total_earned_commission(self, instance):
        # Sum all COMMISSION type changes for this affiliate
        total = CommissionHistory.objects.filter(
            affiliate=instance,
            type=CommissionHistory.COMMISSION
        ).aggregate(total=Sum('change'))['total']
        
        if total is None:
            total = Decimal('0.00')
        return total
    
    def get_total_forwarding_commission(self, instance):
        # Ensure we are summing commissions forwarded to this sub-affiliate's parent
        if not instance.parent_affiliate:
            return Decimal('0.00')

        total = CommissionHistory.objects.filter(
            affiliate=instance.parent_affiliate,
            child_affiliate=instance,
            type=CommissionHistory.COMMISSION
        ).aggregate(total=Sum('change'))['total'] or Decimal('0.00')
        return total
    
class ReferralCodeSerializer(serializers.ModelSerializer):
    user_discount_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Rate between 0 and 1"
    )
    # The clean() method in the model ensures that user_discount_rate + self_commission_rate = 1
    # We will only allow user to set user_discount_rate and automatically computed inside model
    # If you want to show user the computed self_commission_rate, we can make it read-only.
    self_commission_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4, read_only=True
    )
    referral_count = serializers.SerializerMethodField()
    total_earned_commission = serializers.SerializerMethodField()

    class Meta:
        model = ReferralCode
        fields = [
            'id',
            'affiliate',
            'code',
            'user_discount_rate',
            'self_commission_rate',
            'created_at',
            'referral_count',
            'total_earned_commission'
        ]
        read_only_fields = ['id', 'created_at', 'affiliate']
        
    def create(self, validated_data):
        # The authenticated user is retrieved from the request context
        request_user = self.context['request'].user
        validated_data['affiliate'] = request_user.affiliate
        return super().create(validated_data)
    
    def get_referral_count(self, instance):
        # Count how many referrals are associated with this referral code
        return instance.referrals.count()
    
    def get_total_earned_commission(self, obj):
        # Get all referred users who registered using this referral code
        referred_users = obj.referrals.values_list('referred_user', flat=True)

        if not referred_users:
            return Decimal('0.00')

        # Sum all commission type earnings from these referred users
        total = CommissionHistory.objects.filter(
            user_who_paid__in=referred_users,
            type=CommissionHistory.COMMISSION
        ).aggregate(total=Sum('change'))['total']

        return total if total is not None else Decimal('0.00')
    
class ReferralSerializer(serializers.ModelSerializer):
    # Use SlugRelatedField to accept referral_code as a string (the 'code' field)
    referral_code = serializers.SlugRelatedField(
        queryset=ReferralCode.objects.all(),
        slug_field='code'
    )
    class Meta:
        model = Referral
        fields = [
            'id',
            'referred_user',
            'referral_code',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'referred_user']
        
    def validate(self, attrs):
        referred_user = self.context['request'].user
        referral_code = attrs.get('referral_code')
        
        # Check if related_user already has a referral
        if Referral.objects.filter(referred_user=referred_user).exists():
            raise serializers.ValidationError({"error": "REFERRAL_ALREADY_EXISTS", "message": "You have already been referred."})
        # Check if the referral_code belongs to the same user as referred_user
        if referral_code.affiliate.user == referred_user:
            raise serializers.ValidationError({"error": "INVALID_REFERRAL_CODE", "message": "You cannot refer yourself."})
        
    def to_representation(self, instance):
        # Get the original representation
        ret = super().to_representation(instance)
        
        # Replace referred_user with user.uuid
        ret['referred_user'] = instance.referred_user.uuid
        
        # referral_code is already a string because we used SlugRelatedField with slug_field='code'
        # So no need to modify referral_code in representation.
        
        return ret

class ReferralCommissionQueryParamsSerializer(serializers.Serializer):
    """
    Serializer to validate query parameters for commission calculation.
    Adjust fields as needed based on your actual query parameters.
    """
    user = serializers.UUIDField(required=True)
    initial_profit = serializers.DecimalField(max_digits=20, decimal_places=8, required=True)
    apply_to_deposit = serializers.BooleanField(default=False)
    trade_uuid = serializers.UUIDField(required=False)
    
class AffiliateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateRequest
        fields = ['id', 'user', 'contact', 'url', 'description', 'parent_affiliate_code', 'status', 'requested_at', 'reviewed_at', 'admin_note']
        read_only_fields = ['id', 'user', 'status', 'requested_at', 'reviewed_at', 'authorized_by', 'admin_note']
        
    def validate(self, attrs):
        request_user = self.context['request'].user
        existing_requests = AffiliateRequest.objects.filter(user=request_user)
        
        # If you want to ensure the user has no requests at all:
        if existing_requests.exists():
            raise serializers.ValidationError({"error": "REQUEST_EXISTS", "message": "You already have a request reigstered."})
        
        # Check whether parent_affiliate_code in attrs is valid
        parent_affiliate_code = attrs.get('parent_affiliate_code')
        if parent_affiliate_code:
            try:
                Affiliate.objects.get(affiliate_code=parent_affiliate_code)
            except Affiliate.DoesNotExist:
                raise serializers.ValidationError({"error": "INVALID_PARENT_CODE", "message": "Invalid parent affiliate code."})
        
        return attrs

    def create(self, validated_data):
        # The authenticated user is retrieved from the request context
        request_user = self.context['request'].user
        validated_data['user'] = request_user
        # When a user creates a request, it should always start with PENDING.
        validated_data['status'] = AffiliateRequest.STATUS_PENDING
        return super().create(validated_data)
    
class CommissionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionHistory
        fields = ['id', 'affiliate', 'service_type', 'type', 'trade_uuid', 'change', 'balance', 'created_at']
        read_only_fields = ['id', 'affiliate', 'service_type', 'type', 'trade_uuid', 'change', 'balance', 'created_at']
        
class CommissionBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionBalance
        fields = ['id', 'affiliate', 'balance', 'last_update']
        read_only_fields = ['id', 'affiliate', 'balance', 'last_update']
