#!/usr/bin/env python3
import logging
import random
import sys

import numpy as np
from durations import Duration

from timeeval import TimeEval, Datasets
from timeeval.params import IndependentParameterGrid
from timeeval.remote import RemoteConfiguration
from timeeval.resource_constraints import ResourceConstraints, GB
from timeeval.utils.metrics import Metric
from timeeval_experiments.algorithm_configurator import AlgorithmConfigurator
from timeeval_experiments.algorithms import *
from timeeval_experiments.baselines import Baselines


# Setup logging
logging.basicConfig(
    filename="timeeval.log",
    filemode="a",
    level=logging.DEBUG,
    # force=True,
    format="%(asctime)s %(levelname)6.6s - %(name)20.20s: %(message)s",
)

random.seed(42)
np.random.rand(42)


def main():
    dm = Datasets("../../data/test-cases")
    # configurator = AlgorithmConfigurator(config_path="param-config.json")

    # Select datasets and algorithms
    # datasets = dm.select()
    # datasets = random.sample(datasets, 200)
    datasets = [
        "sinus-diff-count-5.semi-supervised",
        # "ecg-diff-count-5.unsupervised",
        # "poly-diff-count-5.unsupervised",
        # "sinus-combined-diff-2.unsupervised"
    ]
    datasets = [("GutenTAG", d) for d in datasets]
    print(f"Selected datasets: {len(datasets)}")

    algorithms = [
        # arima(),
        # autoencoder(),
        # bagel(),
        # cblof(),
        # cof(),
        # copod(),
        # dae(),
        # dbstream(),
        # deepant(),
        # deepnap(),
        # donut(),
        # dspot(),
        # dwt_mlead(),
        # eif(),
        # encdec_ad(),
        # ensemble_gi(),
        # fast_mcd(),
        # fft(),
        # generic_rf(),
        # generic_xgb(),
        # grammarviz3(),
        # hbos(),
        # health_esn(),
        # hif(),
        # hotsax(),
        # hybrid_knn(),
        # iforest(),
        # if_lof(),
        # img_embedding_cae(),
        # kmeans(),
        # knn(),
        # laser_dbn(),
        # left_stampi(),
        # lof(),
        # lstm_ad(),
        # lstm_vae(),
        # median_method(),
        # mscred(),
        # mtad_gat(),
        # multi_hmm(),
        # norma(),
        # normalizing_flows(),
        # novelty_svr(),
        # numenta_htm(),
        # ocean_wnn(),
        # omnianomaly(skip_pull=True, params=IndependentParameterGrid(
        #     param_grid={
        #         "rnn_hidden_size": [100, 200, 300],
        #         "linear_hidden_size": [50, 100, 200],
        #     },
        #     default_params={
        #         "window_size": "heuristic:PeriodSizeHeuristic(factor=1.0, fb_value=100)",
        #         "epochs": 2,
        #         "rnn_hidden_size": 200,
        #         "nf_layers": 5,
        #         "linear_hidden_size": 100
        #     }
        # )),
        # pcc(),
        # pci(),
        # phasespace_svm(),
        # pst(),
        # random_black_forest(),
        # robust_pca(),
        # sarima(),
        # series2graph(),
        # sr(),
        # sr_cnn(),
        # ssa(),
        # stamp(),
        # stomp(),
        # subsequence_fast_mcd(),
        # subsequence_if(),
        # subsequence_lof(),
        # s_h_esd(),
        # tanogan(),
        # tarzan(),
        # telemanom(),
        # torsk(),
        # triple_es(),
        # ts_bitmap(),
        # valmod(),
        Baselines.random(),
        Baselines.increasing(),
        Baselines.normal()
    ]

    print(f"Selected algorithms: {len(algorithms)}\n\n")
    sys.stdout.flush()

    # configurator.configure(algorithms, perform_search=True, ignore_optimized=True)

    print("\nParameter configurations:")
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
        tasks_per_host=4,
        task_cpu_limit=1.,
        task_memory_limit=1 * GB,
        train_fails_on_timeout=False,
        train_timeout=Duration("10m"),
        execute_timeout=Duration("10m"),
    )
    timeeval = TimeEval(dm, datasets, algorithms,
                        repetitions=1,
                        distributed=True,
                        remote_config=cluster_config,
                        resource_constraints=limits,
                        skip_invalid_combinations=True,
                        metrics=[Metric.ROC_AUC],
                        )

    timeeval.run()
    print(timeeval.get_results(aggregated=True, short=True))


if __name__ == "__main__":
    main()
