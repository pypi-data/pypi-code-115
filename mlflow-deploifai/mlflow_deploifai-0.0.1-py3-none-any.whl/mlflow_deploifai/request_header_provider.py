import os
from mlflow.tracking.request_header.abstract_request_header_provider import RequestHeaderProvider
from mlflow.tracking.fluent import active_run, _get_experiment_id, get_experiment


class DeploifaiRequestHeaderProvider(RequestHeaderProvider):
  def in_context(self):
    return True

  def request_headers(self):
    added_headers = {}

    _deploifai_run_id = os.environ.get("USER_EXPERIMENT_RUN_ID", default="")
    if _deploifai_run_id is not "":
      added_headers.update({"deploifai-runid": _deploifai_run_id})

    _run = active_run()
    if _run is not None:
      added_headers.update({"mlflow-runid": _run.info.run_id})

    experiment_id = str(_get_experiment_id())
    added_headers.update({"experiment": experiment_id, "client": "deploifai"})

    return added_headers
