import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose._column_transformer import _check_X
from sklearn.utils import _safe_indexing
from sklearn.utils.validation import _check_feature_names_in
from sklearn.feature_selection import mutual_info_regression


class MutualInfoFilter(TransformerMixin, BaseEstimator):

    def __init__(self, *, alpha=0.0, **kwargs):
        assert np.issubdtype(type(alpha), np.number)
        self.alpha = alpha
        self.kwargs = kwargs

    def get_params(self, deep=True):
        
        kwargs = super().get_params(deep) 
        kwargs.update(**self.kwargs)

        return kwargs

    def fit(self, X, y, *_):
        self._check_feature_names(X, reset=True)
        X = _check_X(X)
        self._check_n_features(X, reset=True)

        select_columns = []
        mi_scores = []
        for col in range(self.n_features_in_):
            x = _safe_indexing(X, col, axis=1)
            if hasattr(x, "iloc"):
                mask = x.isna().to_numpy()
            else:
                if np.issubdtype(x.dtype, np.number):
                    mask = np.isnan(x)
                else:
                    mask = x == None
            if np.issubdtype(x.dtype, np.number):
                x_ = x[~mask]
            else:
                x_, _  = x[~mask].factorize()
            x_ = np.atleast_2d(x_).T
            y_ = y[~mask]
            mi = mutual_info_regression(x_, y_, random_state=0, **self.kwargs)
            assert mi.size == 1
            mi = mi.take(0)
            if mi > self.alpha:
                select_columns.append(col)
            mi_scores.append(mi)
        self.select_columns_ = select_columns
        self.mi_scores_ = mi_scores

        return self

    def transform(self, X):
        self._check_feature_names(X, reset=False)
        X = _check_X(X)
        self._check_n_features(X, reset=False)

        return _safe_indexing(X, self.select_columns_, axis=1)

    def get_feature_names_out(self, input_features=None):
        input_features = _check_feature_names_in(self, input_features)

        return _safe_indexing(input_features, self.select_columns_)
