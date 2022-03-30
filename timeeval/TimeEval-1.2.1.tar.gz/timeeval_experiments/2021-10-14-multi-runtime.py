#!/usr/bin/env python3
import logging
import random
import sys

import numpy as np
from durations import Duration

from timeeval import TimeEval, Datasets
from timeeval.constants import HPI_CLUSTER
from timeeval.remote import RemoteConfiguration
from timeeval.resource_constraints import ResourceConstraints
from timeeval.utils.metrics import Metric
from timeeval_experiments.algorithm_configurator import AlgorithmConfigurator
from timeeval_experiments.algorithms import *
from timeeval_experiments.baselines import Baselines


# Setup logging
logging.basicConfig(
    filename="timeeval.log",
    filemode="a",
    level=logging.INFO,
    # force=True,
    format="%(asctime)s %(levelname)6.6s - %(name)20.20s: %(message)s",
)

random.seed(42)
np.random.rand(42)


def main():
    dm = Datasets("../../data/test-cases", create_if_missing=False)
    configurator = AlgorithmConfigurator(config_path="param-config.json")

    # Select datasets and algorithms
    datasets = dm.select()
    datasets = [(collection, name) for (collection, name) in datasets
                if name.startswith("sinus-channels-single")]
    # datasets = random.sample(datasets, 200)
    print(f"Selected datasets: {len(datasets)}")

    algorithms = [
        normalizing_flows(),
        lof(),
    ]

    print("Parameter configurations:")
    configurator.configure(algorithms,
                           ignore_optimized=True,
                           perform_search=False,
                           assume_parameter_independence=True
                           )

    print("=====================================================================================")
    for algo in algorithms:
        print(algo.name)
        for param in algo.param_grid:
            print(f"  {param}")
    print("=====================================================================================\n\n")
    sys.stdout.flush()

    cluster_config = RemoteConfiguration(
        scheduler_host="localhost",
        worker_hosts=["localhost"]
    )
    limits = ResourceConstraints(
        tasks_per_host=2,
        task_cpu_limit=1.,
        train_fails_on_timeout=False,
        train_timeout=Duration("20m"),
        execute_timeout=Duration("20m"),
    )
    timeeval = TimeEval(dm, datasets, algorithms,
                        repetitions=1,
                        distributed=True,
                        remote_config=cluster_config,
                        resource_constraints=limits,
                        force_training_type_match=True,
                        metrics=[Metric.ROC_AUC],
                        )

    timeeval.run()
    print(timeeval.get_results(aggregated=True, short=True))


if __name__ == "__main__":
    main()
