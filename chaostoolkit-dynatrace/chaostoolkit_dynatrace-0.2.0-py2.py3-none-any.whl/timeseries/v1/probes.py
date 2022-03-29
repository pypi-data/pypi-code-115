# -*- coding: utf-8 -*-
from chaoslib.exceptions import ActivityFailed
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosdynatrace import api_client

__all__ = ["failure_rate"]


def failure_rate(
    entity: str,
    relative_time: str,
    failed_percentage: int,
    configuration: Configuration,
    secrets: Secrets = None,
) -> bool:
    """
    Validates the failure rate of a specific service.
    Returns true if the failure rate is less than the expected failure rate
    For more information check the api documentation.
    https://www.dynatrace.com/support/help/dynatrace-api/environment-api/metric-v1/
    """  # noqa: E501
    params = {
        "timeseriesId": "com.dynatrace.builtin:service.failurerate",
        "relativeTime": relative_time,
        "aggregationType": "AVG",
        "entity": entity,
    }

    result = {}
    with api_client(configuration, secrets) as client:
        r = client.get("/api/v1/timeseries", params=params)

        if r.status_code != 200:
            raise ActivityFailed(f"Dynatrace query {params} failed: {r.text}")

        result = r.json()

    acum = 0
    count = 0
    for x in result.get("result").get("dataPoints").get(entity):
        if x[1] is not None:
            acum = acum + x[1]
            count = count + 1

    if count and ((acum / count) < failed_percentage):
        logger.debug(f"failed rate percentage '{acum/count}'")
        return True
    return False
