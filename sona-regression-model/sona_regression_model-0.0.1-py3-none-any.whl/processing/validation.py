from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, ValidationError

from regression_model.config.core import config


def drop_col_inputs(*, input_data: pd.DataFrame) -> pd.DataFrame:
    """Check model inputs for na values and filter."""
    validated_data = input_data.copy()
    new_vars_with_na = [
        var
        for var in validated_data.columns
        if var
        not in config.model_config.all_features
    ]
    validated_data.drop(new_vars_with_na,axis=1, inplace=True)

    return validated_data

# def validate_inputs(*, input_data: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[dict]]:
#     """Check model inputs for unprocessable values."""
#
#     # convert syntax error field names (beginning with numbers)
#     # input_data.rename(columns=config.model_config.variables_to_rename, inplace=True)
#     # input_data["MSSubClass"] = input_data["MSSubClass"].astype("O")
#     # relevant_data = input_data[config.model_config.features].copy()
#     validated_data = drop_na_inputs(input_data=relevant_data)
#     errors = None
#
#     try:
#         # replace numpy nans so that pydantic can validate
#         MultipleHouseDataInputs(
#             inputs=validated_data.replace({np.nan: None}).to_dict(orient="records")
#         )
#     except ValidationError as error:
#         errors = error.json()
#
#     return validated_data, errors
#
#
class HouseDataInputSchema(BaseModel):
    bed: Optional[str]
    bathroom: Optional[int]
    year_built: Optional[str]
    heating: Optional[str]
    Property_type: Optional[str]
    area: Optional[float]
    county: Optional[float]
    zipcode: Optional[str]

class MultipleHouseDataInputs(BaseModel):
    inputs: List[HouseDataInputSchema]
