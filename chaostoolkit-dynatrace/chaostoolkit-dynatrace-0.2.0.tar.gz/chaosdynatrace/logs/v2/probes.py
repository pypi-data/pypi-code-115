# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Union

from chaoslib.exceptions import ActivityFailed
from chaoslib.types import Configuration, Secrets

from chaosdynatrace import api_client

__all__ = ["get_search_logs", "get_aggregate_logs"]


def get_search_logs(
    from_time: str = "now",
    to_time: str = None,
    query: str = None,
    limit: int = 1000,
    sort: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[Dict[str, Any]]:
    """
    Query the search logs v2 endpoint matching the criteria.

    Returns a list such as:

    ```python
    ```

    https://www.dynatrace.com/support/help/dynatrace-api/environment-api/log-monitoring-v2/get-search-logs
    """  # noqa: E501
    params = {"limit": limit}

    if from_time:
        params["from"] = from_time

    if to_time:
        params["to"] = to_time

    if query is not None:
        params["query"] = query

    if sort is not None:
        params["sort"] = sort

    result = []
    with api_client(configuration, secrets) as client:
        while True:
            r = client.get("/api/v2/logs/search", params=params)

            if r.status_code != 200:
                raise ActivityFailed(
                    f"Dynatrace query {params} failed: {r.text}"
                )

            response = r.json()
            result.extend(response["results"])
            if response["nextSliceKey"] in ("null", None):
                break

            # can't use these with a next page key
            params.clear()
            params["nextSliceKey"] = response["nextSliceKey"]

    return result


def get_aggregate_logs(
    from_time: str = "now",
    to_time: str = None,
    query: str = None,
    time_buckets: int = 1,
    max_group_values: int = 10,
    group_by: Union[str, List[str]] = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Query the aggregate logs v2 endpoint matching the criteria.

    Returns a list such as:

    ```python
    ```

    https://www.dynatrace.com/support/help/dynatrace-api/environment-api/log-monitoring-v2/get-search-logs
    """  # noqa: E501
    params = {}

    if from_time:
        params["from"] = from_time

    if to_time:
        params["to"] = to_time

    if query is not None:
        params["query"] = query

    if group_by is not None:
        params["groupBy"] = (
            group_by if isinstance(group_by) else ",".join(group_by)
        )

    if max_group_values is not None:
        params["maxGroupValues"] = max_group_values

    if time_buckets is not None:
        params["timeBuckets"] = time_buckets

    with api_client(configuration, secrets) as client:
        r = client.get("/api/v2/logs/aggregate", params=params)

        if r.status_code != 200:
            raise ActivityFailed(f"Dynatrace query {params} failed: {r.text}")

        response = r.json()
        return response
