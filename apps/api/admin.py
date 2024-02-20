from django import forms
from django.contrib import admin

from unfold.admin import ModelAdmin
from unfold.widgets import SELECT_CLASSES

from api.models import Permission
from api.utils import get_api_permission_choices


class PermissionForm(forms.ModelForm):
    codename = forms.ChoiceField(
        choices=get_api_permission_choices,
        required=True,
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )

    class Meta:
        model = Permission
        fields = ("codename",)


class PermissionAdmin(ModelAdmin):
    list_display = ["name", "codename"]
    search_fields = ["name", "codename"]
    form = PermissionForm

    def save_model(self, request, obj, form, change):
        if not change:
            codename = form["codename"].value()
            obj.name = dict(form.fields["codename"].choices)[codename]

        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Permission, PermissionAdmin)
