import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class ExtractLetterTransformer(BaseEstimator, TransformerMixin):
    """ To extract the first letter from cabin feature """

    def __init__(self, variables):

        if not isinstance(variables, list):
            raise ValueError("variables should be a list")
        self.variables = variables

    def fit(self, X, y=None):
        """ We need this to fit to sklearn pipeline """
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """ Extract the first letter """
        # so that we do not overwrite the original data
        X = X.copy()
        for feature in self.variables:
            X[feature] = X[feature].str[0]

        return X
