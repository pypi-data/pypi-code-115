
from collections.abc import Iterable
from functools import reduce


def filter_df(df, filter_dict, filter_type='and', filter_iterable_values = True):
    """
    Filter a dataframe with a dictionary of filters.
    """
    views = []
    for key, value in filter_dict.items():
        if filter_iterable_values and not isinstance(value, str) and isinstance(value, Iterable):
            views.append(df[df[key].isin(value)])
        else:
            views.append(df[df[key] == value])
    
    if filter_type == "and":
        index = reduce(lambda x, y : x.index.intersection(y.index), views)   
    elif filter_type == "or":
        index = reduce(lambda x, y : x.index.union(y.index), views)
        
    if len(index) > 0:
        return df.loc[index]
