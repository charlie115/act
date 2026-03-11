def list_slice(lst, n):
    sliced_nested_list = []
    for i in range(n):
        sliced_nested_list.append(lst[i::n])
    return sliced_nested_list