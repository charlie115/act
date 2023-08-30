from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User, UserFavoriteSymbols, UserProfile, UserManagers


class CustomUserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "is_staff")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        new_fieldsets = []
        for name, fieldset in fieldsets:
            if name == "Personal info":
                new_fields = fieldset['fields'] + ('telegram_id', )
                new_fieldsets.append((name, {'fields': new_fields}))
            elif name == "Important dates":
                new_fields = fieldset['fields'] + ('last_username_change', )
                new_fieldsets.append((name, {'fields': new_fields}))
            else:
                new_fieldsets.append((name, fieldset))

        new_fieldsets = tuple(new_fieldsets)

        return new_fieldsets


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserFavoriteSymbols)
admin.site.register(UserProfile)
admin.site.register(UserManagers)
