from rest_framework import serializers
from .models import Coupon, CouponRedemption

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'name', 'amount', 'is_active', 'expires_at', 'created_at']
        read_only_fields = ['id', 'name', 'created_at']
        
from rest_framework import serializers
from .models import CouponRedemption

class CouponRedemptionSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.uuid', read_only=True)
    coupon = serializers.CharField(source='coupon.name', read_only=True)
    class Meta:
        model = CouponRedemption
        fields = ['id', 'user', 'coupon', 'redeemed_at']
        read_only_fields = ['id', 'user', 'coupon', 'redeemed_at']

class RedeemCouponSerializer(serializers.Serializer):
    name = serializers.CharField()

    def validate(self, data):
        name = data.get('name')
        request = self.context['request']
        user = request.user

        try:
            coupon = Coupon.objects.get(name=name)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"error": "INVALID_COUPON_NAME", "message": "Invalid coupon name."})

        if not coupon.is_active:
            raise serializers.ValidationError({"error": "COUPON_INACTIVE", "message": "This coupon is not active."})

        if coupon.is_expired():
            raise serializers.ValidationError({"error": "COUPON_EXPIRED", "message": "This coupon has expired."})

        # Check if the user already redeemed this coupon
        if CouponRedemption.objects.filter(user=user, coupon=coupon).exists():
            raise serializers.ValidationError({"error": "COUPON_ALREADY_REDEEMED", "message": "You have already redeemed this coupon."})

        data['coupon'] = coupon
        return data