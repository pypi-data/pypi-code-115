# -*- coding: utf-8 -*-
from chaoslib.deprecation import warn_about_moved_function
from chaoslib.types import Configuration, Secrets

from chaosdynatrace.timeseries.v1.probes import failure_rate as fr


def failure_rate(
    entity: str,
    relative_time: str,
    failed_percentage: int,
    configuration: Configuration,
    secrets: Secrets = None,
) -> bool:
    """
    !!!DEPRECATED!!!

    Moved to `chaosdynatrace.timeseries.v1.probes`
    """
    warn_about_moved_function(
        "The `chaosdynatrace.probes.failure_rate` probe has moved to "
        "`chaosdynatrace.timeseries.v1.probes.failure_rate`. Please update "
        "your experiment accordingly."
    )
    return fr(entity, relative_time, failed_percentage, configuration, secrets)
