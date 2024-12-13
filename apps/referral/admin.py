from django import forms
from django.contrib import admin
from django.utils import timezone
from decimal import Decimal

from unfold.admin import ModelAdmin
from unfold.widgets import INPUT_CLASSES

from .models import (
    AffiliateTier,
    Affiliate,
    ReferralCode,
    Referral,
    AffiliateRequest,
)

class ReferralCodeForm(forms.ModelForm):
    code = forms.CharField(
        widget=forms.TextInput({"class": " ".join([*INPUT_CLASSES, "w-72"])}),
    )
    user_discount_rate = forms.DecimalField(
        max_digits=5, decimal_places=4,
        widget=forms.NumberInput({"class": " ".join([*INPUT_CLASSES, "w-72"])}),
        help_text="Rate between 0 and 1"
    )
    # self_commission_rate is computed automatically in the model's clean(),
    # so we can mark it as read-only in the admin or just show it.
    # To display it, we can make it read-only or show it as a disabled field.
    # Here, we just display it as read-only in the admin.
    
    def clean_user_discount_rate(self):
        val = self.cleaned_data.get('user_discount_rate')
        if val < Decimal('0') or val > Decimal('1'):
            raise forms.ValidationError("user_discount_rate must be between 0 and 1.")
        return val

    class Meta:
        model = ReferralCode
        fields = "__all__"


class ReferralCodeAdmin(ModelAdmin):
    form = ReferralCodeForm
    list_display = [
        "affiliate",
        "code",
        "user_discount_rate",
        "self_commission_rate",
        "created_at"
    ]
    list_filter = [
        "affiliate__tier__name",
    ]
    search_fields = [
        "affiliate__user__username",
        "code",
    ]
    ordering = ["code"]


class AffiliateTierAdmin(ModelAdmin):
    list_display = [
        "name",
        "base_commission_rate",
        "parent_commission_rate",
        "required_total_commission",
    ]
    search_fields = [
        "name",
    ]


class AffiliateAdmin(ModelAdmin):
    list_display = [
        "user",
        "parent_affiliate",
        "affiliate_code",
        "tier",
        "created_at",
    ]
    list_filter = [
        "tier__name",
    ]
    search_fields = [
        "user__username",
        "affiliate_code",
    ]
    ordering = ["created_at"]
    
class ReferralAdmin(ModelAdmin):
    list_display = [
        "referred_user",
        "referral_code",
        "created_at",
    ]
    search_fields = [
        "referred_user__username",
        "referral_code__code",
    ]
    ordering = ["created_at"]

class AffiliateRequestAdmin(ModelAdmin):
    list_display = [
        "user",
        "status",
        "requested_at",
        "reviewed_at",
        "authorized_by",
    ]
    list_filter = ["status"]
    search_fields = [
        "user__username",
        "user__email",
    ]
    ordering = ["requested_at"]

    # Make requested_at, reviewed_at, and authorized_by read-only
    readonly_fields = ["requested_at", "reviewed_at", "authorized_by"]

    actions = ['approve_requests', 'reject_requests']

    def get_readonly_fields(self, request, obj=None):
        # If editing an existing object, also prevent status from being changed manually here
        # (since we're using actions for status changes)
        if obj and obj.pk:
            return self.readonly_fields + ["status", "user"]
        return self.readonly_fields + ["user"]
    
    # Actions for bulk approving/rejecting AffiliateRequests
    def approve_requests(modeladmin, request, queryset):
        # Approve each selected request
        for ar in queryset:
            if ar.status == AffiliateRequest.STATUS_PENDING or ar.status == AffiliateRequest.STATUS_REJECTED:
                ar.status = AffiliateRequest.STATUS_APPROVED
                ar.authorized_by = request.user
                ar.reviewed_at = timezone.now()
                ar.save()

                # Create affiliate if not exists
                user = ar.user
                if not hasattr(user, 'affiliate'):
                    default_tier = AffiliateTier.objects.get(name="Iron")
                    Affiliate.objects.create(
                        user=user,
                        tier=default_tier,
                    )

    def reject_requests(modeladmin, request, queryset):
        # Reject each selected request
        for ar in queryset:
            if ar.status == AffiliateRequest.STATUS_PENDING:
                ar.status = AffiliateRequest.STATUS_REJECTED
                ar.authorized_by = request.user
                ar.reviewed_at = timezone.now()
                ar.save()
    approve_requests.short_description = "Approve selected requests"
    reject_requests.short_description = "Reject selected requests"


admin.site.register(AffiliateTier, AffiliateTierAdmin)
admin.site.register(Affiliate, AffiliateAdmin)
admin.site.register(ReferralCode, ReferralCodeAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(AffiliateRequest, AffiliateRequestAdmin)