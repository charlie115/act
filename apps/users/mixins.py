from django import forms
from rest_framework import exceptions

from users.models import UserFavoriteAssets


class UserFavoriteAssetsValidatorMixin(object):
    def validate_market_codes(self, market_codes, **kwargs):
        """Validation of market_codes

        If mixin is used in serializer, self will contain the same attributes in serializer.
        If mixin is used in admin, this function has to be added in clean() so we have to pass
        other data in kwargs.
        """

        if "base_asset" in kwargs and "user" in kwargs:
            base_asset = kwargs["base_asset"]
            user = kwargs["user"]
            error = forms.ValidationError(
                {"market_codes": "This set of market codes already exists."}
            )
        elif hasattr(self, "initial_data"):
            base_asset = self.initial_data["base_asset"]
            user = self.context["request"].user
            error = exceptions.ValidationError(
                "This set of market codes already exists."
            )
        else:
            base_asset = None
            error = None

        if user and base_asset and market_codes:
            if len(market_codes) > 2:
                raise forms.ValidationError(
                    {"market_codes": "Select a pair of market codes only."}
                )

            all_market_codes = UserFavoriteAssets.objects.filter(
                base_asset=base_asset, user=user
            ).values_list("market_codes", flat=True)

            all_market_codes = [set(code) for code in all_market_codes]

            if set(market_codes) in all_market_codes:
                raise error

        return market_codes

    def clean(self):
        cleaned_data = super().clean()

        base_asset = cleaned_data.get("base_asset")
        market_codes = cleaned_data.get("market_codes")

        cleaned_data["market_codes"] = self.validate_market_codes(
            market_codes,
            user=self.data["user"],
            base_asset=base_asset,
        )

        return cleaned_data


class UserUUIDSerializerMixin(object):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["user"] = instance.user.uuid

        return data
