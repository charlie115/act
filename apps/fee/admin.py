from django.contrib import admin
from unfold.admin import ModelAdmin

from fee.models import FeeRate, UserFeeLevel
from lib.inlines import NonrelatedTabularInline
from users.models import DepositHistory
from users.utils import get_user_spent_fee

class FeeRateAdmin(ModelAdmin):
    list_display = [
        "level",
        "rate",
        "total_paid_fee_required",
    ]
    list_editable = ["rate", "total_paid_fee_required"]
    ordering = ("level",)


class DepositHistoryInline(NonrelatedTabularInline):
    model = DepositHistory
    # form = DepositHistoryForm
    fields = ["registered_datetime", "change", "balance", "type", "pending"]
    show_change_link = True
    extra = 0

    def get_form_queryset(self, obj):
        return self.model.objects.filter(
            user=obj.user, type=DepositHistory.FEE
        ).order_by("-registered_datetime")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserFeeLevelAdmin(ModelAdmin):
    list_display = [
        "user",
        "fee_level",
        "total_paid_fee",
        "total_paid_fee_realtime",  # Add the new field to display
        "last_updated_datetime",
    ]
    search_fields = ["user__email", "user__username", "total_paid_fee"]
    list_editable = ["fee_level"]
    list_filter = ["fee_level"]
    inlines = [DepositHistoryInline]
    
    def total_paid_fee_realtime(self, obj):
        # Call the utility function to get the real-time fee spent by the user
        return get_user_spent_fee(obj.user)
    total_paid_fee_realtime.short_description = "Total Paid Fee (Real-Time)"


    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(FeeRate, FeeRateAdmin)
admin.site.register(UserFeeLevel, UserFeeLevelAdmin)
