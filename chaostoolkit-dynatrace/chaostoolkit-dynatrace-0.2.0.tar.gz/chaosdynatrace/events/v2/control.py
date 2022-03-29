import getpass
import os
import platform
from datetime import datetime, timezone
from secrets import token_hex
from typing import Any, Dict, List, Union

from chaoslib import experiment_hash
from chaoslib.types import (
    Activity,
    Configuration,
    Experiment,
    Hypothesis,
    Journal,
    Run,
    Secrets,
)
from logzero import logger

try:
    from opentelemetry import trace as trace_api

    HAS_OPENTELEMTRY = True
except ImportError:
    HAS_OPENTELEMTRY = False

from chaosdynatrace import api_client

__all__ = [
    "configure_control",
    "cleanup_control",
    "configure_control",
    "after_experiment_control",
    "before_activity_control",
    "after_activity_control",
    "after_method_control",
    "before_method_control",
    "before_rollback_control",
    "after_rollback_control",
    "before_hypothesis_control",
    "after_hypothesis_control",
]
manager = None


def configure_control(experiment: Experiment):
    global manager
    manager = DynatraceEventManager(experiment)


def cleanup_control(**kwargs):
    global manager
    manager = None


def before_experiment_control(
    context: Experiment = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> None:
    """
    Notify Dynatrace this experiment is in progress
    """
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.experiment_started(context, configuration, dynatrace_secrets)


def after_experiment_control(
    state: Journal,
    context: Experiment = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> None:
    """
    Notify Dynatrace this experiment is not in progress
    any longer.
    """
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.experiment_finished(
        context, state, configuration, dynatrace_secrets
    )


def before_hypothesis_control(
    context: Hypothesis,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.ssh_started(context, configuration, dynatrace_secrets)


def after_hypothesis_control(
    context: Hypothesis,
    state: Dict[str, Any],
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.ssh_finished(context, state, configuration, dynatrace_secrets)


def before_method_control(
    context: Experiment,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.method_started(context, configuration, dynatrace_secrets)


def after_method_control(
    context: Experiment,
    state: List[Run],
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.method_finished(context, state, configuration, dynatrace_secrets)


def before_rollback_control(
    context: Experiment,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.rollback_started(context, configuration, dynatrace_secrets)


def after_rollback_control(
    context: Experiment,
    state: List[Run],
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.rollback_finished(context, state, configuration, dynatrace_secrets)


def before_activity_control(
    context: Activity,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.activity_started(context, configuration, dynatrace_secrets)


def after_activity_control(
    context: Activity,
    state: Run,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    dynatrace_secrets = (secrets or {}).get("dynatrace")
    manager.activity_finished(context, state, configuration, dynatrace_secrets)


###############################################################################
# Private functions
###############################################################################
class DynatraceEventManager:
    def __init__(self, experiment: Experiment) -> None:
        self.run_id = token_hex(16)
        self.experiment_ref = experiment_hash(experiment)
        self.experiment_title = experiment["title"]
        self.experiment_tags = experiment.get("tags", [])

        self.trace_id = None
        self.experiment_span_id = None

    def experiment_started(
        self,
        experiment: Experiment,
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "experiment-started",
            f"Experiment started: {experiment['title']}",
            configuration=configuration,
            secrets=secrets,
        )

    def experiment_finished(
        self,
        experiment: Experiment,
        state: Journal,
        configuration: Configuration,
        secrets: Secrets = None,
    ) -> None:
        self.send(
            "experiment-finished",
            f"Experiment finished: {experiment['title']}",
            state=state,
            configuration=configuration,
            secrets=secrets,
        )

    def activity_started(
        self, activity: Activity, configuration: Configuration, secrets: Secrets
    ) -> None:
        self.send(
            "activity-started",
            f"Activity started: {activity['name']}",
            activity=activity,
            configuration=configuration,
            secrets=secrets,
        )

    def activity_finished(
        self,
        activity: Activity,
        run: Run,
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "activity-finished",
            f"Activity finished: {activity['name']}",
            activity=activity,
            state=run,
            configuration=configuration,
            secrets=secrets,
        )

    def method_started(
        self,
        experiment: Experiment,
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "method-started",
            "Method started",
            configuration=configuration,
            secrets=secrets,
        )

    def method_finished(
        self,
        experiment: Experiment,
        state: List[Run],
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "method-finished",
            "Method finished",
            configuration=configuration,
            secrets=secrets,
        )

    def rollback_started(
        self,
        experiment: Experiment,
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "rollback-started",
            "Rollback started",
            configuration=configuration,
            secrets=secrets,
        )

    def rollback_finished(
        self,
        experiment: Experiment,
        state: List[Run],
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "rollback-finished",
            "Rollback finished",
            configuration=configuration,
            secrets=secrets,
        )

    def ssh_started(
        self,
        hypothesis: Hypothesis,
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "hypothesis-started",
            "Steady state hypothesis started",
            hypothesis=hypothesis,
            configuration=configuration,
            secrets=secrets,
        )

    def ssh_finished(
        self,
        hypothesis: Hypothesis,
        state: Dict[str, Any],
        configuration: Configuration,
        secrets: Secrets,
    ) -> None:
        self.send(
            "hypothesis-finished",
            "Steady state hypothesis finished",
            hypothesis=hypothesis,
            state=state,
            configuration=configuration,
            secrets=secrets,
        )

    def send(
        self,
        event: str,
        content: str,
        activity: Activity = None,
        hypothesis: Hypothesis = None,
        state: Union[Journal, Run, Dict[str, Any]] = None,
        configuration: Configuration = None,
        secrets: Secrets = None,
    ) -> None:

        payload = {
            "content": content,
            "time": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "username": getpass.getuser(),
            "hostname": platform.node(),
            "service.name": "chaostoolkit",
            "log.source": "chaostoolkit",
            "log.tag": self.experiment_tags,
            "chaostoolkit_experiment_ref": self.experiment_ref,
            "chaostoolkit_experiment_event_name": event,
            "chaostoolkit_experiment_run_id": self.run_id,
            "chaostoolkit_experiment_title": self.experiment_title,
        }

        if activity:
            payload["chaostoolkit_activity_name"] = activity["name"]
            if state:
                payload["chaostoolkit_activity_status"] = state["status"]
        elif hypothesis and state:
            payload["chaostoolkit_hypothesis_met"] = state["steady_state_met"]
        elif state:
            payload["chaostoolkit_experiment_status"] = state["status"]
            payload["chaostoolkit_experiment_deviated"] = state["deviated"]

        level = "info"
        if state and (not hypothesis) and (not activity):
            if state["status"] == "interrupted":
                level = "warn"
            elif state["status"] == "failed":
                level = "fail"
            elif state["status"] == "aborted":
                level = "error"
        payload["level"] = level

        if HAS_OPENTELEMTRY:
            # when we have opentelemetry installed, we may try to see
            # if it was enabled for this experiment's run and therefore
            # attach our logs to the traces
            s = trace_api.get_current_span()
            if s.is_recording():
                c = s.get_span_context()
                self.trace_id = trace_api.format_trace_id(c.trace_id)
                self.experiment_span_id = trace_api.format_span_id(c.span_id)

            if self.trace_id:
                payload["dt.trace_id"] = self.trace_id
                payload["trace_id"] = self.trace_id

            if self.experiment_span_id:
                payload["dt.span_id"] = self.experiment_span_id
                payload["span_id"] = self.experiment_span_id

        with api_client(configuration, secrets) as c:
            r = c.post(
                "/api/v2/logs/ingest",
                headers={"Content-Type": "application/json; charset=utf-8"},
                json=payload,
            )
            if r.status_code != 204:
                logger.debug(
                    "Failed to send log event to dynatrace "
                    f"[{r.status_code}] {r.text}"
                )
