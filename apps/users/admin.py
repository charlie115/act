import json

from django import forms
from django.contrib import admin
from django.utils.timezone import now
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
import datetime

from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import INPUT_CLASSES, SELECT_CLASSES

from users.inlines import (
    ProfileInline,
    ManagersInline,
    ManagedInline,
    UserFeeLevelInline,
    DepositHistoryInline,
)
from users.mixins import UserFavoriteAssetsValidatorMixin
from users.models import (
    User,
    UserBlocklist,
    UserFavoriteAssets,
    UserManagement,
    UserRole,
    UserSocialApps,
    DepositBalance,
    DepositHistory,
    WithdrawalRequest,
)
from users.utils import get_user_withdrawable_balance, get_user_withdrawable_commission

from wallet.mixins import WalletMixin
from lib.status import HTTP_200_OK, HTTP_201_CREATED


class UserRoleAdmin(ModelAdmin):
    list_display = ["name", "get_api_permissions"]
    filter_horizontal = ["api_permissions"]
    search_fields = ["name"]
    readonly_fields = ["name"]

    def get_api_permissions(self, obj):
        api_permissions = obj.api_permissions.all()
        return mark_safe(
            "<br>".join(
                [f"{api_permission.name}" for api_permission in api_permissions]
                if api_permissions
                else "-"
            )
        )

    get_api_permissions.short_description = "API Permissions"
    get_api_permissions.allow_tags = True

    def get_readonly_fields(self, request, obj):
        if obj.name in [UserRole.VISITOR, UserRole.USER]:
            return self.readonly_fields + ["api_permissions"]

        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "show_role_customized_color",
    ]
    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "role",
    ]
    search_fields = [
        "email",
        "username",
        "first_name",
        "last_name",
    ]
    readonly_fields = [
        "uuid",
        "date_joined",
        "last_login",
        "last_username_change",
    ]
    ordering = [
        "email",
    ]
    inlines = [
        ProfileInline,
        UserFeeLevelInline,
        ManagersInline,
        ManagedInline,
    ]
    fieldsets = (
        (
            "Overview",
            {
                "classes": ["tab"],
                "fields": (
                    "is_active",
                    "uuid",
                    "email",
                    "password",
                ),
            },
        ),
        (
            _("Personal info"),
            {
                "classes": ["tab"],
                "fields": (
                    "username",
                    ("first_name", "last_name"),
                    "telegram_chat_id",
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "classes": ["tab"],
                "fields": ("is_staff", "role", "groups", "user_permissions"),
            },
        ),
        (
            _("Important dates"),
            {
                "classes": ["tab"],
                "fields": ("date_joined", "last_login", "last_username_change"),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    @display(description=_("Role"), ordering="role", label=True)
    def show_role_customized_color(self, obj):
        return obj.role.name

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ["email", "telegram_chat_id"]
        return self.readonly_fields

    def get_inlines(self, request, obj=None):
        if obj:
            return super().get_inlines(request, obj)
        else:
            return []


# TODO: Group per manager, managed_user
class UserManagementAdmin(ModelAdmin):
    list_display = [
        "manager",
        "managed_user",
    ]
    search_fields = [
        "managed_user__email",
        "managed_user__username",
        "managed_user__first_name",
        "managed_user__last_name",
        "manager___email",
        "manager___username",
        "manager___first_name",
        "manager___last_name",
    ]

    def has_change_permission(self, request, obj=None):
        return False


class UserFavoriteAssetsForm(UserFavoriteAssetsValidatorMixin, forms.ModelForm):
    def get_market_codes_choices():
        with open("apps/infocore/fixtures/infocore.marketcode.json") as f:
            market_codes = json.load(f)
            market_codes = [
                (market_code["fields"]["code"], market_code["fields"]["code"])
                for market_code in market_codes
            ]
            return market_codes

    base_asset = forms.CharField(
        required=True,
        widget=forms.TextInput({"class": " ".join([*INPUT_CLASSES])}),
    )

    market_codes = forms.MultipleChoiceField(
        choices=get_market_codes_choices,
        widget=forms.SelectMultiple(
            {
                "class": " ".join([*SELECT_CLASSES]),
                "size": len(get_market_codes_choices()),
            }
        ),
        help_text="Only select a <b>pair</b> of market codes.",
    )


class UserFavoriteAssetsAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "base_asset",
        "market_codes",
    ]
    search_fields = [
        "user__email",
        "base_asset",
        "market_codes",
    ]
    form = UserFavoriteAssetsForm


class UserBlocklistAdmin(ModelAdmin):
    list_display = [
        "id",
        "target_username",
        "target_ip",
        "datetime",
    ]
    search_fields = [
        "target_username",
        "target_ip",
        "datetime",
    ]

    def has_change_permission(self, request, obj=None):
        return False


class UserSocialAppsAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "socialapp",
    ]
    search_fields = [
        "user__email",
        "user__username",
        "socialapp__name",
        "socialapp__provider",
        "socialapp__clientid",
        "socialapp__secret",
    ]

    def has_change_permission(self, request, obj=None):
        return False


class DepositBalanceAdmin(ModelAdmin):
    list_display = [
        "user",
        "balance",
        "last_update",
    ]
    search_fields = [
        "user",
    ]
    inlines = [DepositHistoryInline]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DepositHistoryAdmin(ModelAdmin):
    list_display = [
        "user",
        "change",
        "balance",
        "type",
        "coupon",
        "pending",
        "registered_datetime",
    ]
    list_filter = (
        "type",
        "pending",
    )
    search_fields = [
        "user__email",
        "user__username",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
class WithdrawalRequestAdmin(ModelAdmin):
    hdwallet_address_endpoint = "user_wallet/"
    hdwallet_balance_endpoint = "user_wallet/balance/"
    hdwallet_transfer_endpoint = "user_wallet/transfer/"
    list_display = ('user', 'get_withdrawable_balance', 'get_actual_usdt_balance', 'get_actual_trx_balance', 'amount', 'type', 'status', 'requested_datetime', 'approved_datetime', 'completed_datetime', 'authorized_by')
    list_filter = ('status', 'type', 'amount')
    search_fields = ('user__email', 'address', 'txid')
    
    # Make some fields read-only if desired. For example:
    readonly_fields = ('requested_datetime', 'user_address', 'address', 'get_withdrawable_balance', 'get_actual_usdt_balance', 'get_actual_trx_balance', 'get_withdrawable_commission', 'amount', 'type', 'txid', 'authorized_by', 'approved_datetime', 'completed_datetime')

    actions = ['approve_withdrawal', 'reject_withdrawal', 'mark_completed']

    def approve_withdrawal(self, request, queryset):
        for wr in queryset.filter(status=WithdrawalRequest.PENDING):
            wr.status = WithdrawalRequest.APPROVED
            wr.approved_datetime = now()
            wr.authorized_by = request.user
            wr.save()

    def reject_withdrawal(self, request, queryset):
        for wr in queryset.filter(status=WithdrawalRequest.PENDING):
            wr.status = WithdrawalRequest.REJECTED
            wr.authorized_by = request.user
            wr.save()

    def mark_completed(self, request, queryset):
        # filter in both APPROVED and PENDING status
        for wr in queryset.filter(status__in=[WithdrawalRequest.APPROVED, WithdrawalRequest.PENDING]):
            # Here you would call hdwallet-service API to execute the withdrawal
            wallet = WalletMixin()
            api_response = wallet.hdwallet_service_create_api(
                endpoint=self.hdwallet_transfer_endpoint,
                data={
                    "user_id": wr.user.id,
                    "asset": "USDT",
                    "amount": wr.amount,
                    "to_address": wr.address,
                }
            )
            if api_response.status_code != HTTP_201_CREATED and api_response.status_code != HTTP_200_OK:
                # Handle the error
                wr.status = WithdrawalRequest.REJECTED
                wr.remark = f"Failed to execute withdrawal, {api_response.json()}"
                wr.authorized_by = request.user
                wr.save()
                continue
            # Suppose we get a txid back:
            txid = api_response.json().get("txid")
            wr.txid = txid
            # Check whether it wasn't APPROVED state, if so also update the approved_datetime
            if wr.status != WithdrawalRequest.APPROVED:
                wr.approved_datetime = now()
            wr.status = WithdrawalRequest.COMPLETED
            wr.completed_datetime = now()
            wr.authorized_by = request.user
            wr.save()
            
            # Update deposit history to reflect the withdrawal
            DepositHistory.objects.create(
                user=wr.user,
                change=-wr.amount,
                type=DepositHistory.WITHDRAW,
                txid=txid,
                description=f"Withdrawal executed to {wr.address}"
            )
            
    def has_add_permission(self, request):
        # Disallow adding new WithdrawalRequests from the admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Allow viewing the changelist but not detail pages
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)
    
    def user_address(self, obj):
        # Return the user's address from hdwallet-service API
        if obj.user:
            wallet = WalletMixin()
            api_response = wallet.hdwallet_service_retrieve_api(
            endpoint=self.hdwallet_address_endpoint,
            path_param=obj.user.id,
            )
            if api_response.status_code == HTTP_200_OK:
                obj = api_response.json()
                return obj["address"]
            else:
                return "-"
        else:
            return "-"

    def get_withdrawable_balance(self, obj):
        # Return the user's withdrawable balance
        if obj.user:
            return get_user_withdrawable_balance(obj.user)
        return "-"
    
    def get_withdrawable_commission(self, obj):
        # Return the user's withdrawable commission balance
        if obj.user:
            return get_user_withdrawable_commission(obj.user)
        return "-"
    
    def get_actual_usdt_balance(self, obj):
        # Return the user's actual USDT balance in HDwallet
        # This would be a call to the hdwallet-service API
        if obj.user:
            wallet = WalletMixin()
            api_response = wallet.hdwallet_service_retrieve_api(
            endpoint=self.hdwallet_balance_endpoint,
            path_param=obj.user.id,
            query_params={"asset": "USDT"},
            )
            if api_response.status_code == HTTP_200_OK:
                obj = api_response.json()
                return obj["balance"]
            else:
                return "-"
        else:
            return "-"
        
    def get_actual_trx_balance(self, obj):
        # Return the user's actual TRX balance in HDwallet
        # This would be a call to the hdwallet-service API
        if obj.user:
            wallet = WalletMixin()
            api_response = wallet.hdwallet_service_retrieve_api(
            endpoint=self.hdwallet_balance_endpoint,
            path_param=obj.user.id,
            query_params={"asset": "TRX"},
            )
            if api_response.status_code == HTTP_200_OK:
                obj = api_response.json()
                return obj["balance"]
            else:
                return "-"
        else:
            return "-"
    
    user_address.short_description = "User Address"
    get_withdrawable_balance.short_description = "Withdrawable Balance"
    get_withdrawable_commission.short_description = "Withdrawable Commission"
    get_actual_usdt_balance.short_description = "Actual USDT Balance"
    get_actual_trx_balance.short_description = "Actual TRX Balance"
    approve_withdrawal.short_description = "Approve selected withdrawal requests"
    reject_withdrawal.short_description = "Reject selected withdrawal requests"
    mark_completed.short_description = "Mark selected requests as completed and execute withdrawal"


admin.site.register(UserBlocklist, UserBlocklistAdmin)
admin.site.register(UserFavoriteAssets, UserFavoriteAssetsAdmin)
admin.site.register(UserManagement, UserManagementAdmin)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(UserSocialApps, UserSocialAppsAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(DepositBalance, DepositBalanceAdmin)
admin.site.register(DepositHistory, DepositHistoryAdmin)
admin.site.register(WithdrawalRequest, WithdrawalRequestAdmin)
