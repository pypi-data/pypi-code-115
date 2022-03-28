import typing as t

# import numpy as np
import pandas as pd

# from classification_model import __version__ as _version
from classification_model.config.core import config
from classification_model.processing.data_manager import load_pipeline
from classification_model.processing.validation import validate_inputs

pipeline_file_name = f"{config.app_config.pipeline_save_file}0.0.1.pkl"
_titanic_pipe = load_pipeline(file_name=pipeline_file_name)


def make_prediction(
    *,
    input_data: t.Union[pd.DataFrame, dict],
) -> dict:
    """Make a prediction using a saved model pipeline."""

    data = pd.DataFrame(input_data)
    validated_data, errors = validate_inputs(input_data=data)
    results = {"predictions": None, "version": "0.0.1", "errors": errors}

    if not errors:
        predictions = _titanic_pipe.predict(
            X=validated_data[config.model_config.features]
        )
        results = {
            "predictions": list(predictions),  # type: ignore
            "version": "0.0.1",
            "errors": errors,
        }

    return results
