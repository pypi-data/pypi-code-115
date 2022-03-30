__version__ = '0.1.0'

from ._min_support import MinSupportTransformer
from ._missing_value_filter import MissingValueFilter
from ._mutual_info_filter import MutualInfoFilter

__all__ = [
    "MinSupportTransformer",
    "MissingValueFilter",
    "MutualInfoFilter",
    "get_p",
]

from sklearn_transformer_extensions.preprocessing import FunctionTransformer
from sklearn_transformer_extensions.compose import make_column_transformer
from sklearn_transformer_extensions.pipeline import make_pipeline
from sklearn.compose import make_column_selector
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from xgboost import XGBRegressor
from sklearn.compose import TransformedTargetRegressor
from sklearn_transformer_extensions.metrics import make_scorer
from sklearn.metrics import mean_squared_log_error
from sklearn.model_selection import KFold, cross_val_score
from functools import partial
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OrdinalEncoder as _OrdinalEncoder
from collections import namedtuple

select_qual = make_column_selector(dtype_include=[object, "category"],
                                   pattern=r'^(?:(?!SalePrice|Id).)*$')
select_quant = make_column_selector(dtype_include=np.number,
                                    pattern=r'^(?:(?!SalePrice|Id).)*$')


def set_zero(X):
    X[X == 0] = np.nan
    return X


def set_1950(X):
    X[X == 1950] = np.nan
    return X


# Numerical features
ct1 = make_column_transformer(
    (FunctionTransformer(set_zero), [
        'MasVnrArea', 'BsmtFinSF1', 'BsmtFinSF2', 'TotalBsmtSF', 'GarageArea',
        '2ndFlrSF'
    ]),
    (FunctionTransformer(set_1950), ['YearRemodAdd']),
    remainder='passthrough',
    verbose_feature_names_out=False,
)

ct2 = make_column_transformer(
    (MinSupportTransformer(min_support=50, fill_value=None), select_qual),
    remainder='passthrough', verbose_feature_names_out=False)

ct3 = make_column_transformer(
    (MissingValueFilter(method='ratio', alpha=0.7), select_qual),
    remainder='passthrough', verbose_feature_names_out=False)

select_qual_wo_bldgtype = lambda df: [
    c for c in select_qual(df) if c != 'BldgType'
]

ct4 = make_column_transformer(
    (MutualInfoFilter(alpha=1e-3,
                      discrete_features=True), select_qual_wo_bldgtype),
    (MutualInfoFilter(alpha=1e-3, discrete_features=False), select_quant),
    ("passthrough", ["BldgType"]), remainder='drop',
    verbose_feature_names_out=False)

ct5 = FunctionTransformer(
    lambda X: X.astype({c: "category"
                        for c in select_qual(X)}))


class OrdinalEncoder(_OrdinalEncoder):

    def get_feature_names_out(self, input_features=None):
        return input_features




ct6 = make_column_transformer((OrdinalEncoder(
    handle_unknown='use_encoded_value', unknown_value=-1), select_qual),
                              remainder='passthrough',
                              verbose_feature_names_out=False)

ct7 = make_column_transformer((FunctionTransformer(lambda df: df.fillna(-1))))

p1 = make_pipeline(ct1, 'passthrough', xy_adapter=True)
p2 = make_pipeline(ct1, ct2, 'passthrough', xy_adapter=True)
p3 = make_pipeline(ct1, ct2, ct3, 'passthrough', xy_adapter=True)
p4 = make_pipeline(ct1, ct2, ct3, ct4, 'passthrough', xy_adapter=True)
p5 = make_pipeline(ct1, ct2, ct3, ct4, ct5, 'passthrough', xy_adapter=True)
p7 = make_pipeline(ct1, ct2, ct3, ct4, ct5, ct6, 'passthrough', xy_adapter=True)

xgbr = TransformedTargetRegressor(
    XGBRegressor(objective='reg:squarederror', tree_method='gpu_hist', gpu_id=0,
                 enable_categorical=True), func=np.log1p, inverse_func=np.expm1)
lr = TransformedTargetRegressor(LinearRegression(), func=np.log1p,
                                inverse_func=np.expm1)

p6_xgbr = make_pipeline(ct1, ct2, ct3, ct4, ct5, xgbr, xy_adapter=True)
p6_lr = make_pipeline(ct1, ct2, ct3, ct4, ct5, lr, xy_adapter=True)

p7_xgbr = make_pipeline(ct1, ct2, ct3, ct4, ct5, ct6, xgbr, xy_adapter=True)
p7_lr = make_pipeline(ct1, ct2, ct3, ct4, ct5, ct6, lr, xy_adapter=True)

scorer = make_scorer(mean_squared_log_error, greater_is_better=False,
                     squared=False)

kfolds = KFold(n_splits=10, shuffle=True, random_state=42)


def score_fn(model, X, y):
    scores = -cross_val_score(estimator=model, X=X, y=y, scoring=scorer,
                              cv=kfolds, n_jobs=10, verbose=0)
    return float(f"{np.mean(scores):.4f}"), float(f"{np.std(scores):.4f}")


def get_p():
    tup = namedtuple('NamedTuple', [
        'p1', 'p2', 'p3', 'p4', 'p5', 'p6_xgbr', 'p6_lr', 'p7', 'p7_xgbr',
        'p7_lr'
    ])
    return tup(p1, p2, p3, p4, p5, p6_xgbr, p6_lr, p7, p7_xgbr, p7_lr)
