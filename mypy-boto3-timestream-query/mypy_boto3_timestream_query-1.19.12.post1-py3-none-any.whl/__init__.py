"""
Main interface for timestream-query service.

Usage::

    ```python
    from boto3.session import Session
    from mypy_boto3_timestream_query import (
        Client,
        QueryPaginator,
        TimestreamQueryClient,
    )

    session = Session()
    client: TimestreamQueryClient = session.client("timestream-query")

    query_paginator: QueryPaginator = client.get_paginator("query")
    ```
"""
from .client import TimestreamQueryClient
from .paginator import QueryPaginator

Client = TimestreamQueryClient


__all__ = ("Client", "QueryPaginator", "TimestreamQueryClient")
