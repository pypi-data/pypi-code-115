import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose._column_transformer import _check_X
from sklearn.utils import _safe_indexing
from typing import Iterable
from sklearn.utils.validation import _check_feature_names_in


class MissingValueFilter(TransformerMixin, BaseEstimator):

    def __init__(self, method, alpha):
        assert method in ['ratio', 'count']
        self.method = method

        assert np.issubdtype(type(alpha), np.number)
        self.alpha = alpha

    def fit(self, X, y=None, *_):
        self._check_feature_names(X, reset=True)
        X = _check_X(X)
        self._check_n_features(X, reset=True)

        select_columns = []
        for col in range(self.n_features_in_):
            x = _safe_indexing(X, col, axis=1)
            if hasattr(x, "iloc"):
                mask = x.isna().to_numpy()
            else:
                if np.issubdtype(x.dtype, np.number):
                    mask = np.isnan(x)
                else:
                    mask = x == None
            if self.method == 'ratio' and mask.mean() < self.alpha:
                select_columns.append(col)
            elif self.method == 'count' and mask.sum() < self.alpha:
                select_columns.append(col)
        self.select_columns_ = select_columns

        return self

    def transform(self, X):
        self._check_feature_names(X, reset=False)
        X = _check_X(X)
        self._check_n_features(X, reset=False)

        return _safe_indexing(X, self.select_columns_, axis=1)

    def get_feature_names_out(self, input_features=None):
        input_features = _check_feature_names_in(self, input_features)

        return _safe_indexing(input_features, self.select_columns_)
