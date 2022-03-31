"""
Main interface for finspace-data service.

Usage::

    ```python
    from boto3.session import Session
    from mypy_boto3_finspace_data import (
        Client,
        FinSpaceDataClient,
    )

    session = Session()
    client: FinSpaceDataClient = session.client("finspace-data")
    ```
"""
from .client import FinSpaceDataClient

Client = FinSpaceDataClient


__all__ = ("Client", "FinSpaceDataClient")
