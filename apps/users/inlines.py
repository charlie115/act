from django import forms
from unfold.admin import TabularInline, StackedInline
from unfold.admin import UnfoldBooleanWidget

from lib.inlines import NonrelatedTabularInline
from fee.models import UserFeeLevel
from users.models import UserManagement, UserProfile, DepositHistory


class ProfileInline(StackedInline):
    model = UserProfile
    verbose_name = "Profile"
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ManagersInline(TabularInline):
    fk_name = "managed_user"
    model = UserManagement
    extra = 0
    verbose_name = "Manager"
    classes = ("collapse",)

    def has_change_permission(self, request, obj=None):
        return False


class ManagedInline(TabularInline):
    fk_name = "manager"
    model = UserManagement
    extra = 0
    verbose_name = "Managed user"
    classes = ("collapse",)

    def has_change_permission(self, request, obj=None):
        return False


class UserFeeLevelInline(TabularInline):
    model = UserFeeLevel
    verbose_name = "Fee Level"
    classes = ("collapse",)
    readonly_fields = ["fee_level", "total_paid_fee", "last_updated_datetime"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DepositHistoryForm(forms.ModelForm):
    pending = forms.BooleanField(widget=UnfoldBooleanWidget())

    class Meta:
        model = DepositHistory
        fields = "__all__"


class DepositHistoryInline(NonrelatedTabularInline):
    model = DepositHistory
    form = DepositHistoryForm
    fields = ["registered_datetime", "change", "balance", "type", "pending"]
    show_change_link = True
    extra = 0

    def get_form_queryset(self, obj):
        return self.model.objects.filter(user=obj.user).order_by("-registered_datetime")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
