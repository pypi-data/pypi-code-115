def sort_dict_by_key(_dict):
    return dict(sorted(
        _dict.items(),
        key=lambda x: x[0],
    ))
