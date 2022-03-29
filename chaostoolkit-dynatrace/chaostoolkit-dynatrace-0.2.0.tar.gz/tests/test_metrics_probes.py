import respx
from httpx import Response

from chaosdynatrace.metrics.v2.probes import query_data_points


def test_query_data_points_with_defaults(respx_mock):
    m = respx.get(
        url="https://xxxxx.live.dynatrace.com/api/v2/metrics/query",
        params={"metricSelector": "*", "resolution": "5m", "from": "now"},
    ).mock(
        return_value=Response(
            200,
            json={
                "totalCount": 1,
                "nextPageKey": "null",
                "resolution": "1h",
                "result": [
                    {
                        "metricId": "",
                        "data": [
                            {
                                "dimensions": [],
                                "dimensionMap": {},
                                "timestamps": [
                                    1647545100000,
                                    1647545400000,
                                    1647545700000,
                                    1647546000000,
                                    1647546300000,
                                    1647546600000,
                                    1647546900000,
                                ],
                                "values": [
                                    None,
                                    9272.911109076605,
                                    3565.171102555593,
                                    3441.491649373372,
                                    48242.974005126955,
                                    8055.613537597656,
                                    None,
                                ],
                            }
                        ],
                    }
                ],
            },
        )
    )

    result = query_data_points(
        configuration={
            "dynatrace_base_url": "https://xxxxx.live.dynatrace.com"
        },
        secrets={"token": "xyz"},
    )

    assert m.called
    assert result != []


def test_query_data_points_pages(respx_mock):
    m = respx.get(
        url="https://xxxxx.live.dynatrace.com/api/v2/metrics/query",
        params={"metricSelector": "*", "resolution": "5m", "from": "now"},
    ).mock(
        return_value=Response(
            200,
            json={
                "totalCount": 1,
                "nextPageKey": "1",
                "resolution": "1h",
                "result": [
                    {
                        "metricId": "",
                        "data": [
                            {
                                "dimensions": [],
                                "dimensionMap": {},
                                "timestamps": [
                                    1647545100000,
                                    1647545400000,
                                    1647545700000,
                                    1647546000000,
                                    1647546300000,
                                    1647546600000,
                                    1647546900000,
                                ],
                                "values": [
                                    None,
                                    9272.911109076605,
                                    3565.171102555593,
                                    3441.491649373372,
                                    48242.974005126955,
                                    8055.613537597656,
                                    None,
                                ],
                            }
                        ],
                    }
                ],
            },
        )
    )

    m = respx.get(
        url="https://xxxxx.live.dynatrace.com/api/v2/metrics/query",
        params={
            "nextPageKey": "1",
        },
    ).mock(
        Response(
            200,
            json={
                "totalCount": 1,
                "nextPageKey": "null",
                "resolution": "1h",
                "result": [
                    {
                        "metricId": "",
                        "data": [
                            {
                                "dimensions": [],
                                "dimensionMap": {},
                                "timestamps": [
                                    1647545100000,
                                    1647545400000,
                                    1647545700000,
                                    1647546000000,
                                    1647546300000,
                                    1647546600000,
                                    1647546900000,
                                ],
                                "values": [
                                    None,
                                    9272.911109076605,
                                    3565.171102555593,
                                    3441.491649373372,
                                    48242.974005126955,
                                    8055.613537597656,
                                    None,
                                ],
                            }
                        ],
                    }
                ],
            },
        )
    )

    result = query_data_points(
        configuration={
            "dynatrace_base_url": "https://xxxxx.live.dynatrace.com"
        },
        secrets={"token": "xyz"},
    )

    assert m.called
    assert result != []
    assert len(result) == 2
