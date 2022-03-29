# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Union

from chaoslib.exceptions import ActivityFailed
from chaoslib.types import Configuration, Secrets

from chaosdynatrace import api_client

__all__ = ["query_data_points"]


def query_data_points(
    metrics_selector: Union[str, List[str]] = "*",
    entity_selector: Union[str, List[str]] = None,
    resolution: str = "5m",
    from_time: str = "now",
    to_time: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> List[Dict[str, Any]]:
    """
    Query the metrics v2 endpoint for any data point matching the various
    parameters.

    Returns a list such as:

    ```python
    [
        {
            'metricId': 'builtin:tech.generic.network.bytesRx:splitBy():avg:auto:sort(value(avg,descending)):limit(10)',
            'data': [
                {
                    'dimensions': [],
                    'dimensionMap': {},
                    'timestamps': [
                        1647545100000,
                        1647545400000,
                        1647545700000,
                        1647546000000,
                        1647546300000,
                        1647546600000,
                        1647546900000
                    ],
                    'values': [
                        None,
                        9272.911109076605,
                        3565.171102555593,
                        3441.491649373372,
                        48242.974005126955,
                        8055.613537597656,
                        None
                    ]
                }
            ]
        }
    ]
    ```

    https://www.dynatrace.com/support/help/dynatrace-api/environment-api/metric-v2/get-data-points
    """  # noqa: E501
    params = {}

    if metrics_selector is not None:
        metrics_selector = (
            metrics_selector
            if isinstance(metrics_selector, str)
            else ",".join(metrics_selector)
        )

    if entity_selector is not None:
        entity_selector = (
            entity_selector
            if isinstance(entity_selector, str)
            else ",".join(entity_selector)
        )

    if resolution:
        params["resolution"] = resolution

    if from_time:
        params["from"] = from_time

    if to_time:
        params["to"] = to_time

    if metrics_selector is not None:
        params["metricSelector"] = metrics_selector

    if entity_selector is not None:
        params["entitySelector"] = entity_selector

    result = []
    with api_client(configuration, secrets) as client:
        while True:
            r = client.get("/api/v2/metrics/query", params=params)

            if r.status_code != 200:
                raise ActivityFailed(
                    f"Dynatrace query {params} failed: {r.text}"
                )

            response = r.json()
            result.extend(response["result"])
            if response["nextPageKey"] in ("null", None):
                break

            # can't use these with a next page key
            params.clear()
            params["nextPageKey"] = response["nextPageKey"]

    return result
