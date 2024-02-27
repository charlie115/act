from django_filters import BaseCSVFilter, CharFilter, FilterSet


class CharArrayFilter(BaseCSVFilter, CharFilter):
    pass


class UserUuidFilter(FilterSet):
    user = CharFilter(field_name="user__uuid", lookup_expr="exact")


def filter_list_of_dictionaries(dict_params, data_to_filter):
    """Utility function to filter a list of dictionaries with a given dictionary of parameters.

    Arguments:
        dict_params -- dict params with key, values to filter
        data_to_filter -- list of dict data to filter

    Returns:
        _description_
    """

    filtered_data = filter(
        lambda item: all((item[k] == v for (k, v) in dict_params.items())),
        data_to_filter,
    )

    return filtered_data
