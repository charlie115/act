from rest_framework import serializers
from decimal import Decimal

from fee.models import UserFeeLevel, FeeRate
from users.utils import get_user_spent_fee


class UserFeeLevelSerializer(serializers.ModelSerializer):
    fee_rate = serializers.SerializerMethodField()
    realtime_total_paid_fee = serializers.SerializerMethodField()
    required_paid_fee_to_next_level = serializers.SerializerMethodField()

    class Meta:
        model = UserFeeLevel
        fields = [
            'fee_level', 
            'total_paid_fee', 
            'last_updated_datetime', 
            'fee_rate',
            'realtime_total_paid_fee',
            'required_paid_fee_to_next_level'
        ]
        read_only_fields = [
            'fee_level', 
            'total_paid_fee', 
            'last_updated_datetime', 
            'fee_rate',
            'realtime_total_paid_fee',
            'required_paid_fee_to_next_level'
        ]

    def get_fee_rate(self, obj):
        try:
            fee_rate = FeeRate.objects.get(level=obj.fee_level)
            return fee_rate.rate
        except FeeRate.DoesNotExist:
            return None
    
    def get_realtime_total_paid_fee(self, obj):
        # Get the real-time total paid fee using the utility function
        return -1 * get_user_spent_fee(obj.user)
    
    def get_required_paid_fee_to_next_level(self, obj):
        # Get the real-time total paid fee
        realtime_total_paid_fee = -1 * get_user_spent_fee(obj.user)
        
        # Get the next fee level
        next_level = obj.fee_level + 1
        
        # Get the fee rate required for the next level
        try:
            next_fee_rate = FeeRate.objects.get(level=next_level)
            required_fee = next_fee_rate.total_paid_fee_required
            
            # Calculate the difference
            remaining_fee = required_fee - realtime_total_paid_fee
            
            # Return 0 if the user has already paid enough for the next level
            return max(Decimal('0'), remaining_fee)
        
        except FeeRate.DoesNotExist:
            # No next level exists, return 0 or None
            return Decimal('0') 