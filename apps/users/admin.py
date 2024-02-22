from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from allauth.socialaccount.models import SocialAccount
from unfold.admin import ModelAdmin, TabularInline, StackedInline

from users.mixins import UserFavoriteAssetsValidatorMixin
from users.models import (
    User,
    UserRole,
    UserBlocklist,
    UserFavoriteAssets,
    UserManagement,
    UserProfile,
    UserSocialApps,
)


class ProfileInline(StackedInline):
    model = UserProfile
    verbose_name = "Profile"
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FavoriteAssetsInline(TabularInline):
    model = UserFavoriteAssets
    verbose_name = "Favorite asset"
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
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


class SocialAppInline(TabularInline):
    model = UserSocialApps
    extra = 0
    verbose_name = "Social app"
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SocialAccountInline(StackedInline):
    model = SocialAccount
    verbose_name = "Social account"
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserRoleAdmin(ModelAdmin):
    list_display = ["name", "get_api_permissions"]
    search_fields = [
        "name",
    ]
    filter_horizontal = ["api_permissions"]
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


class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "role",
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
    inlines = (
        ProfileInline,
        SocialAccountInline,
        ManagersInline,
        ManagedInline,
        FavoriteAssetsInline,
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "is_active",
                    "uuid",
                    ("first_name", "last_name"),
                    ("username", "email"),
                    "telegram_chat_id",
                    "password",
                    "date_joined",
                    ("last_login", "last_username_change"),
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": ("is_staff", "role", "groups"),
                "classes": ("collapse",),
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
    pass


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


admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(UserBlocklist, UserBlocklistAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserManagement, UserManagementAdmin)
