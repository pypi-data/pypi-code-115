# -*- coding: utf-8 -*-
import pytest
from chaoslib.exceptions import InvalidExperiment

from chaosdynatrace import api_client


def test_failed_when_missing_base_url():
    with pytest.raises(InvalidExperiment) as ex:
        with api_client(configuration={}, secrets={}):
            pass
    assert "Missing the `dynatrace_base_url` configuration value" in str(
        ex.value
    )


def test_failed_when_missing_token():
    with pytest.raises(InvalidExperiment) as ex:
        with api_client(
            configuration={"dynatrace_base_url": "https://test"}, secrets={}
        ):
            pass
    assert "Missing the `dynatrace`/`token` secret value" in str(ex.value)


def test_succeeds_creating_client():
    with api_client(
        configuration={"dynatrace_base_url": "https://test"},
        secrets={"token": "xyz"},
    ) as c:
        assert c.base_url == "https://test"
        assert c.headers["Authorization"] == "Api-Token xyz"
