import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose._column_transformer import _check_X
from sklearn.utils import _safe_indexing
from typing import Iterable
from sklearn.utils.validation import _check_feature_names_in


class MinSupportTransformer(TransformerMixin, BaseEstimator):
    """For each column, sets values that have low support to a fill_value.

    Attributes
    ----------
    min_support: int, Required
        The minimum support required for a category to exist. Categories that
        have less support than `min_support` are overwritten by `fill_value`.
    fill_value: scalar, None, pd.NA, np.nan, Required
        If a category has less support than `min_support`, it is overwritten by
        this value.

    Parameters
    ----------
    high_support_: dict[col, list]
        Dictionary mapping each column to the values that have high support.


    >>> import pandas as pd
    >>> import numpy as np
    >>> from sklearn.utils._testing import assert_array_equal
    >>> from house_prices import MinSupportTransformer
    >>> df = pd.DataFrame({
    ...     "col1": np.r_[1, 2, 2, 2, 3, 3],
    ...     "col2": np.r_[1, 1, 2, 3, 3, 3],
    ... })
    >>> exp = pd.DataFrame({
    ...     "col1": np.r_[np.nan, 2, 2, 2, 3, 3],
    ...     "col2": np.r_[1, 1, np.nan, 3, 3, 3],
    ... })
    >>> ms = MinSupportTransformer(2, np.nan)
    >>> assert_array_equal(exp, ms.fit_transform(df))
    >>> df_test = pd.DataFrame({
    ...     "col1": np.r_[2, 1, 2, 2, 1, 3],
    ...     "col2": np.r_[2, 1, 2, 3, 2, 3],
    ... })
    >>> exp_test = pd.DataFrame({
    ...     "col1": np.r_[2, np.nan, 2, 2, np.nan, 3],
    ...     "col2": np.r_[np.nan, 1, np.nan, 3, np.nan, 3],
    ... })
    >>> assert_array_equal(exp_test, ms.transform(df_test))

    It also works for numpy arrays.
    >>> X = np.c_[[1, 2, 2, 2, 3, 3], [1, 1, 2, 3, 3, 3]]
    >>> ms = MinSupportTransformer(2, np.nan)
    >>> assert_array_equal(exp, ms.fit_transform(X))
    >>> X_test = np.c_[[2, 1, 2, 2, 1, 3], [2, 1, 2, 3, 2, 3]]
    >>> assert_array_equal(exp_test, ms.transform(X_test))

    >>> X = np.c_[["a", "b", "b", "b", "c", "c"], 
    ...           ["a", "a", "b", "c", "c", "c"]]
    >>> exp = np.c_[[None, "b", "b", "b", "c", "c"], 
    ...             ["a", "a", None, "c", "c", "c"]]
    >>> ms = MinSupportTransformer(2, None)
    >>> assert_array_equal(exp, ms.fit_transform(X))
    >>> X_test = np.c_[["b", "a", "b", "b", "a", "c"], 
    ...                ["b", "a", "b", "c", "b", "c"]]
    >>> exp_test = np.c_[["b", None, "b", "b", None, "c"], 
    ...                  [None, "a", None, "c", None, "c"]]
    >>> assert_array_equal(exp_test, ms.transform(X_test))
    >>> exp_na = np.c_[[pd.NA, "b", "b", "b", "c", "c"], 
    ...                ["a", "a", pd.NA, "c", "c", "c"]]
    >>> ms = MinSupportTransformer(2, pd.NA)
    
    pd.NA arrays are not directly comparable even if they are equal.
    >>> assert_array_equal(pd.DataFrame(exp_na).fillna("HELLO"), 
    ...                    pd.DataFrame(ms.fit_transform(X)).fillna("HELLO"))

    It also works when the initial array has NaNs.
    >>> ms = MinSupportTransformer(2, None)
    >>> X = np.c_[["a", None, "b", "b", "c", "c"], 
    ...           ["a", "a", "b", None, "c", "c"]]
    >>> exp = np.c_[[None, None, "b", "b", "c", "c"], 
    ...             ["a", "a", None, None, "c", "c"]]
    >>> assert_array_equal(exp, ms.fit_transform(X))

    """

    def __init__(self, min_support, fill_value):
        assert np.issubdtype(type(min_support), np.number)
        self.min_support = min_support

        assert not isinstance(fill_value, Iterable)
        self.fill_value = fill_value

    def fit(self, X, y=None, *_):

        self._check_feature_names(X, reset=True)
        X = _check_X(X)
        self._check_n_features(X, reset=True)

        high_support = {}
        for col in range(self.n_features_in_):
            x = _safe_indexing(X, col, axis=1)
            if hasattr(x, "iloc"):
                mask = x.isna().to_numpy()
            else:
                if np.issubdtype(x.dtype, np.number):
                    mask = np.isnan(x)
                else:
                    mask = x == None
            uvals, cnts = np.unique(x[~mask], return_counts=True)
            high_support[col] = uvals[cnts >= self.min_support]
        self.high_support_ = high_support

        return self

    def transform(self, X):

        self._check_feature_names(X, reset=False)
        X = _check_X(X).copy()
        self._check_n_features(X, reset=False)

        if not hasattr(X, "iloc"):
            X = X.astype(np.result_type(type(self.fill_value), X))

        Xind = X
        if hasattr(X, "iloc"):
            Xind = X.iloc  # type: ignore

        for col in range(self.n_features_in_):
            high_support = self.high_support_[col]
            Xind[~np.isin(Xind[:, col], high_support), col] = self.fill_value

        return X

    def get_feature_names_out(self, input_features=None):
        return input_features

