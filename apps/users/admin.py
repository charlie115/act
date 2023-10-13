from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from unfold.admin import ModelAdmin, TabularInline, StackedInline

from users.mixins import UserFavoriteAssetsValidatorMixin
from users.models import (
    User,
    UserBlocklist,
    UserFavoriteAssets,
    UserProfile,
    UserManagers,
)


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
    model = UserManagers
    extra = 0
    verbose_name = "Manager"

    def has_change_permission(self, request, obj=None):
        return False


class ManagedInline(TabularInline):
    fk_name = "manager"
    model = UserManagers
    extra = 0
    verbose_name = "Managed user"

    def has_change_permission(self, request, obj=None):
        return False


class SocialAccountInline(StackedInline):
    model = SocialAccount
    verbose_name = "Social account"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
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
    inlines = (
        ProfileInline,
        ManagersInline,
        ManagedInline,
        SocialAccountInline,
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "is_active",
                    "uuid",
                    ("username", "email"),
                    "password",
                    ("date_joined", "last_login", "last_username_change"),
                )
            },
        ),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "telegram_id")},
        ),
        (
            _("Permissions"),
            {
                "fields": ("is_staff", "role", "groups"),
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

    def get_inlines(self, request, obj=None):
        if obj:
            return super().get_inlines(request, obj)
        else:
            return []


# TODO: Group per manager, managed_user
class UserManagersAdmin(ModelAdmin):
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


class UserFavoriteAssetsForm(UserFavoriteAssetsValidatorMixin, forms.ModelForm):
    pass


# TODO: Move to User
class UserFavoriteAssetsAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "base_asset",
        "market_codes",
    ]
    search_fields = [
        "base_asset",
        "market_codes",
    ]
    form = UserFavoriteAssetsForm


class UserBlocklistAdmin(ModelAdmin):
    list_display = [
        "id",
        "target_email",
        "target_ip",
        "datetime",
    ]
    search_fields = [
        "target_email",
        "target_ip",
        "datetime",
    ]

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(UserBlocklist, UserBlocklistAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserManagers, UserManagersAdmin)
admin.site.register(UserFavoriteAssets, UserFavoriteAssetsAdmin)

admin.site.unregister(EmailAddress)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)

admin.site.unregister(Site)
