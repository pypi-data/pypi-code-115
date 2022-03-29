# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import List

import httpx
from chaoslib.discovery.discover import (
    discover_probes,
    initialize_discovery_result,
)
from chaoslib.exceptions import InvalidExperiment
from chaoslib.types import (
    Configuration,
    DiscoveredActivities,
    Discovery,
    Secrets,
)
from logzero import logger

__all__ = ["api_client", "discover"]
__version__ = "0.2.0"


@contextmanager
def api_client(
    configuration: Configuration, secrets: Secrets = None
) -> httpx.Client:
    """
    Configure a HTTP client with the appropriate base url and authentication
    header set.

    The token should be provided as a secret like this:

    ```json
    {
        "dynatrace": {
            "token": "..."
        }
    }
    ```

    Make sure the token has the right permissions to perform API call.

    The configuration should hold the base url with the environment id:

    ```json
    {
        "dynatrace_base_url": "https://{your-env-id}.live.dynatrace.com"
    }
    """
    configuration = configuration or {}
    base = configuration.get("dynatrace_base_url")
    dynatrace = configuration.get("dynatrace")
    if not base:
        if dynatrace:
            logger.warn(
                "You are passing the Dynatrace base url as a block when it "
                "should rather be a string."
            )
            base = dynatrace.get("dynatrace_base_url")

    # still not found, bail
    if not base:
        raise InvalidExperiment(
            "Missing the `dynatrace_base_url` configuration value"
        )

    secrets = secrets or {}
    token = secrets.get("token")
    if not token:
        if dynatrace:
            token = dynatrace.get("dynatrace_token")
            if token:
                logger.warn(
                    "You are passing the Dynatrace token via the "
                    "configuration. This should be updated to use a secret "
                    "instead."
                )

    # still not found, bail
    if not token:
        raise InvalidExperiment("Missing the `dynatrace`/`token` secret value")

    headers = headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Token {token}",
    }

    with httpx.Client(base_url=base, headers=headers) as c:
        yield c


def discover(discover_system: bool = True) -> Discovery:
    """
    Discover Dynatrace capabilities from this extension.
    """
    logger.info("Discovering capabilities from chaostoolkit-dynatrace")

    discovery = initialize_discovery_result(
        "chaostoolkit-dynatrace", __version__, "dynatrace"
    )
    discovery["activities"].extend(load_exported_activities())

    return discovery


###############################################################################
# Private functions
###############################################################################
def load_exported_activities() -> List[DiscoveredActivities]:
    """
    Extract metadata from actions and probes exposed by this extension.
    """
    activities = []
    activities.extend(discover_probes("chaosdynatrace.logs.v2.probes"))
    activities.extend(discover_probes("chaosdynatrace.metrics.v2.probes"))
    activities.extend(discover_probes("chaosdynatrace.timeseries.v1.probes"))

    return activities
