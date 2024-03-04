import json

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import INPUT_CLASSES, SELECT_CLASSES

from users.inlines import (
    ProfileInline,
    ManagersInline,
    ManagedInline,
    DepositHistoryInline,
)
from users.mixins import UserFavoriteAssetsValidatorMixin
from users.models import (
    User,
    UserBlocklist,
    UserFavoriteAssets,
    UserManagement,
    UserRole,
    DepositBalance,
    DepositHistory,
)


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
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "show_role_customized_color",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "role",
    )
    search_fields = [
        "email",
        "username",
        "first_name",
        "last_name",
        "profile__referral",
    ]
    readonly_fields = (
        "uuid",
        "date_joined",
        "last_login",
        "last_username_change",
    )
    ordering = ("email",)
    inlines = (
        ProfileInline,
        ManagersInline,
        ManagedInline,
    )
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
            return self.readonly_fields + ("email", "telegram_chat_id")
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
        "balance",
        "change",
        "type",
        "pending",
        "registered_datetime",
    ]
    list_filter = (
        "type",
        "pending",
    )
    search_fields = [
        "user",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(UserFavoriteAssets, UserFavoriteAssetsAdmin)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(UserBlocklist, UserBlocklistAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserManagement, UserManagementAdmin)
admin.site.register(DepositBalance, DepositBalanceAdmin)
admin.site.register(DepositHistory, DepositHistoryAdmin)
