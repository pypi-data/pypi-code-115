import pytest
import respx
from httpx import Response

from chaosdynatrace.probes import failure_rate


def test_probe_has_moved(respx_mock):
    with pytest.deprecated_call():
        respx.get(
            url="https://xxxxx.live.dynatrace.com/api/v1/timeseries",
            params=dict(
                timeseriesId="com.dynatrace.builtin:service.failurerate",
                relativeTime="now",
                aggregationType="AVG",
                entity="ENTITY",
            ),
        ).mock(
            return_value=Response(
                200, json={"result": {"dataPoints": {"ENTITY": [(0, None)]}}}
            )
        )

        failure_rate(
            entity="ENTITY",
            relative_time="now",
            failed_percentage=100,
            configuration={
                "dynatrace_base_url": "https://xxxxx.live.dynatrace.com"
            },
            secrets={"token": "xyz"},
        )
