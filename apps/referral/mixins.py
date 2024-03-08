from django import forms
from rest_framework import exceptions


class ReferralCodeMixin(object):
    def validate_origin_market_code(self, origin_market_code):
        error_message = "origin_market_code cannot be the same as target_market_code"

        if hasattr(self, "initial_data"):
            data = self.initial_data
            error = exceptions.ValidationError(error_message)
        else:
            data = self.data
            error = forms.ValidationError({"origin_market_code": error_message})

        if data["target_market_code"] == origin_market_code:
            raise error

        return origin_market_code

    def clean(self):
        cleaned_data = super().clean()

        cleaned_data["origin_market_code"] = self.validate_origin_market_code(
            cleaned_data.get("origin_market_code")
        )

        return cleaned_data
