import io
from typing import Dict

import pandas as pd

from algoralabs.common.requests import __post_request
from algoralabs.data.transformations.response_transformers import no_transform
from algoralabs.decorators.data import data_request


@data_request(transformer=no_transform)
def analyze_data(data: pd.DataFrame) -> Dict[str, any]:  # TODO replace with typed object
    endpoint = f"data-engine/alpha/analyze"

    parquet_bytes = data.to_parquet()
    return __post_request(endpoint, files={'file': parquet_bytes})


@data_request(process_response=lambda r: r.content, transformer=lambda r: pd.read_parquet(io.BytesIO(r)))
def transform_data(data: pd.DataFrame) -> pd.DataFrame:
    endpoint = f"data-engine/alpha/transform"

    parquet_bytes = data.to_parquet()
    return __post_request(endpoint, files={'file': parquet_bytes})
