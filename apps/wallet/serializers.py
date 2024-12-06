from rest_framework import serializers
from users.models import User, UserRole

class UserWalletQueryParamsSerializer(serializers.Serializer):
    user = serializers.UUIDField(required=True)
    
    def validate(self, attrs):
        # If user_id provided, ensure it matches authenticated user
        user_uuid = attrs.get('user')
        request = self.context['request']
        
        if request.user.role.name == UserRole.ADMIN:
            attrs['user_id'] = User.objects.get(uuid=user_uuid).id
            return attrs
        
        if user_uuid != request.user.uuid:
            raise serializers.ValidationError(
                "Cannot access wallet information for other users"
            )
            
        # Always use authenticated user's ID
        # Use pk instead of uuid to send it to hdwallet service
        attrs['user_id'] = request.user.id
        return attrs
    
class UserWalletBalanceQueryParmasSerializer(serializers.Serializer):
    user = serializers.UUIDField(required=True)
    
    def validate(self, attrs):
        # If user_id provided, ensure it matches authenticated user
        user_uuid = attrs.get('user')
        request = self.context['request']
        
        if request.user.role.name == UserRole.ADMIN:
            attrs['user_id'] = User.objects.get(uuid=user_uuid).id
            return attrs
        
        if user_uuid != request.user.uuid:
            raise serializers.ValidationError(
                "Cannot access wallet information for other users"
            )
            
        # Always use authenticated user's ID
        # Use pk instead of uuid to send it to hdwallet service
        attrs['user_id'] = request.user.id
        return attrs

class UserWalletTransactionBodyParamsSerializer(serializers.Serializer):
    user = serializers.UUIDField(required=True)
    asset = serializers.CharField(default="USDT")
    deposit_only = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        # If user_id provided, ensure it matches authenticated user
        user_uuid = attrs.get('user')
        request = self.context['request']
        
        if request.user.role.name == UserRole.ADMIN:
            attrs['user_id'] = User.objects.get(uuid=user_uuid).id
            return attrs
        
        if user_uuid != request.user.uuid:
            raise serializers.ValidationError(
                "Cannot access wallet information for other users"
            )
            
        # Always use authenticated user's ID
        # Use pk instead of uuid to send it to hdwallet service
        attrs['user_id'] = request.user.id
        return attrs
    