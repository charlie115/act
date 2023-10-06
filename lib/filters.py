from django_filters import BaseCSVFilter, CharFilter, FilterSet


class CharArrayFilter(BaseCSVFilter, CharFilter):
    pass


class UserUuidFilter(FilterSet):
    user = CharFilter(field_name="user__uuid", lookup_expr="exact")
