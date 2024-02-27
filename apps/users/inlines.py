from allauth.socialaccount.models import SocialAccount
from unfold.admin import TabularInline, StackedInline

from users.models import (
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
