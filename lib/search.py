from bisect import bisect_left


def search_closest_number(search_list, search_number):
    """Assumes search_list is sorted. Returns closest value to search_number."""

    pos = bisect_left(search_list, search_number)

    if pos == 0:
        return search_list[0]
    if pos == len(search_list):
        return search_list[-1]

    before = search_list[pos - 1]
    after = search_list[pos]

    if after - search_number < search_number - before:
        return after
    else:
        return before
