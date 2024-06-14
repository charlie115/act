from django import forms
from django.contrib import admin

from unfold.admin import ModelAdmin
from unfold.widgets import INPUT_CLASSES, SELECT_CLASSES

from infocore.models import MarketCode
from referral.mixins import ReferralCodeMixin
from referral.models import ReferralCode, ReferralGroup, Referral


class ReferralCodeForm(ReferralCodeMixin, forms.ModelForm):
    code = forms.CharField(
        widget=forms.TextInput({"class": " ".join([*INPUT_CLASSES, "w-72"])}),
    )
    target_market_code = forms.ModelChoiceField(
        queryset=MarketCode.objects.all(),
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )
    origin_market_code = forms.ModelChoiceField(
        queryset=MarketCode.objects.all(),
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )
    contact = forms.CharField(
        required=False,
        widget=forms.TextInput({"class": " ".join([*INPUT_CLASSES, "w-72"])}),
    )

    class Meta:
        model = ReferralCode
        fields = "__all__"


class ReferralCodeAdmin(ModelAdmin):
    form = ReferralCodeForm
    list_display = [
        "user",
        "referral_group",
        "target_market_code",
        "origin_market_code",
        "code",
        "max_depth",
    ]
    list_filter = [
        "target_market_code",
        "origin_market_code",
        "max_depth",
        "referral_group__name",
    ]
    search_fields = [
        "user__email",
        "code",
    ]
    ordering = ["code"]


class ReferralGroupAdmin(ModelAdmin):
    list_display = [
        "name",
        "commission_rate",
        "upper_share_rate",
        "description",
    ]
    search_fields = [
        "name",
    ]


class ReferralAdmin(ModelAdmin):
    list_display = [
        "referred_user",
        "referral_code",
        "registered_datetime",
    ]
    search_fields = [
        "referred_user__email",
        "referral_code__code",
    ]


admin.site.register(ReferralCode, ReferralCodeAdmin)
admin.site.register(ReferralGroup, ReferralGroupAdmin)
admin.site.register(Referral, ReferralAdmin)
