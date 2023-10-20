import math
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.utils import html


class CharacterSeparatedField(serializers.ListField):
    """
    Character separated ListField.
    Based on https://gist.github.com/jpadilla/8792723.
    A field that separates a string with a given separator into
    a native list and reverts a list into a string separated with a given
    separator.
    """

    def __init__(self, *args, **kwargs):
        self.separator = kwargs.pop("separator", ",")
        self.empty = kwargs.pop("empty", ",")
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data = data.split(self.separator)
        return super().to_internal_value(data)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
            # Don't return [] if the update is partial
            if self.field_name not in dictionary:
                if getattr(self.root, "partial", False):
                    return empty
                return dictionary.get(self.field_name, empty)
            return dictionary.get(self.field_name)

        return dictionary.get(self.field_name, empty)

    def to_representation(self, data):
        data = super().to_representation(data)
        return self.separator.join(data)


class FloatOrNoneField(serializers.FloatField):
    def to_representation(self, value):
        return None if math.isnan(value) else float(value)
