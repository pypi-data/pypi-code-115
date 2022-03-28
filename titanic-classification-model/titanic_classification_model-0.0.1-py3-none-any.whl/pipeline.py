from feature_engine.encoding import OneHotEncoder, RareLabelEncoder
from feature_engine.imputation import (
    AddMissingIndicator,
    CategoricalImputer,
    MeanMedianImputer,
)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from classification_model.config.core import config
from classification_model.processing import features as pp

titanic_pipe = Pipeline(
    [
        # imputate categorical missing data with 'missing'
        (
            "categorical_missing",
            CategoricalImputer(
                imputation_method="missing",
                variables=config.model_config.categorical_variables,
            ),
        ),
        # add a missing indicator for numerical variables
        (
            "missing_indicator",
            AddMissingIndicator(variables=config.model_config.numerical_variables),
        ),
        # impute numerical variables with median values
        (
            "fill_num_mean",
            MeanMedianImputer(
                imputation_method="median",
                variables=config.model_config.numerical_variables,
            ),
        ),
        # extracting first letter from cabin data
        (
            "extract_first_letter",
            pp.ExtractLetterTransformer(variables=config.model_config.cabin),
        ),
        # == CATEGORICAL ENCODING ======
        # remove categories present in less than 5% of the observations (0.05)
        # group them in one category called 'Rare'
        (
            "rare_label_encoder",
            RareLabelEncoder(
                tol=0.05,
                n_categories=1,
                variables=config.model_config.categorical_variables,
            ),
        ),
        # encode categorical variables with One Hot encoding
        (
            "one_hot_encoder",
            OneHotEncoder(
                drop_last=True, variables=config.model_config.categorical_variables
            ),
        ),
        # scaling the data
        ("scaler", StandardScaler()),
        # Logistic Regression
        (
            "logistic_regression",
            LogisticRegression(
                C=config.model_config.C, random_state=config.model_config.random_state
            ),
        ),
    ]
)
