from django.contrib import admin
from .models import Coupon, CouponRedemption

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'amount', 'is_active', 'expires_at', 'created_at']
    list_filter = ['is_active', 'expires_at']
    search_fields = ['name', 'code']
    ordering = ['created_at']
    readonly_fields = ['code', 'created_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'amount', 'is_active', 'expires_at')
        }),
        ('Automatically Generated Fields', {
            'fields': ('code', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'coupon', 'redeemed_at']
    search_fields = ['user__username', 'coupon__name', 'coupon__code']
    list_filter = ['redeemed_at']
    ordering = ['redeemed_at']
    readonly_fields = ['redeemed_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'coupon', 'redeemed_at')
        }),
    )