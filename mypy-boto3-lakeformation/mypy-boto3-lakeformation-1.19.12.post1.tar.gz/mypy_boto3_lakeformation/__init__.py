"""
Main interface for lakeformation service.

Usage::

    ```python
    from boto3.session import Session
    from mypy_boto3_lakeformation import (
        Client,
        LakeFormationClient,
    )

    session = Session()
    client: LakeFormationClient = session.client("lakeformation")
    ```
"""
from .client import LakeFormationClient

Client = LakeFormationClient


__all__ = ("Client", "LakeFormationClient")
