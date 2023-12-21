from django.contrib import admin
from django.contrib.sites.models import Site

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from unfold.admin import ModelAdmin, TabularInline

from socialaccounts.models import ProxySocialAccount, ProxySocialApp, ProxySocialToken
from users.models import UserSocialApps


class SocialAppUsersInline(TabularInline):
    model = UserSocialApps
    extra = 0
    verbose_name = "User"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProxySocialAccountAdmin(ModelAdmin):
    list_display = ("user", "uid", "provider")
    list_filter = ("provider",)
    search_fields = ("user", "uid", "provider")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    class Meta:
        model = ProxySocialAccount


class ProxySocialAppAdmin(ModelAdmin):
    list_display = (
        "name",
        "provider",
    )
    inlines = (SocialAppUsersInline,)

    class Meta:
        model = ProxySocialApp


class ProxySocialTokenAdmin(ModelAdmin):
    class Meta:
        model = ProxySocialToken


admin.site.unregister(Site)
admin.site.unregister(EmailAddress)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)

admin.site.register(ProxySocialAccount, ProxySocialAccountAdmin)
admin.site.register(ProxySocialApp, ProxySocialAppAdmin)
# admin.site.register(ProxySocialToken, ProxySocialTokenAdmin)
