import respx
from httpx import Response

from chaosdynatrace.probes import failure_rate


def test_compute_failure_rate(respx_mock):
    m = respx.get(
        url="https://xxxxx.live.dynatrace.com/api/v1/timeseries",
        params=dict(
            timeseriesId="com.dynatrace.builtin:service.failurerate",
            relativeTime="now",
            aggregationType="AVG",
            entity="ENTITY",
        ),
    ).mock(
        return_value=Response(
            200, json={"result": {"dataPoints": {"ENTITY": [(0, 1)]}}}
        )
    )

    assert failure_rate(
        entity="ENTITY",
        relative_time="now",
        failed_percentage=100,
        configuration={
            "dynatrace_base_url": "https://xxxxx.live.dynatrace.com"
        },
        secrets={"token": "xyz"},
    )

    assert m.called
