#!/usr/bin/env python
"""
this is the routine setup of ams 
run the code from commandline by

run_ams -input <the parameter input filename>

"""

import argparse
import logging
import numpy as np
import time

from pyfile_utils import Config, instantiate, load_callable

from pysampling.sampling_routines import (
    Sampling,
    TransitionPathSampling,
    CommittorAnalysis,
)

default_config = dict(root="./", seed=10000)


def main(args=None):

    config = parse_command_line(args)

    start = time.time()

    random_state = np.random.RandomState(seed=config.seed)
    config.np_random_state = random_state

    try:
        sampling_class = load_callable("pysampling.sampling_routines." + config.method)
    except:
        sampling_class = load_callable(config.method)

    instance = sampling_class(**dict(config))

    # run initial MD or obtain initial configs
    start_configs = instance.obtain_init_configs()

    # run iteration
    instance.run(start_configs)

    # print statistics
    instance.stats()

    end = time.time()

    logging.info(f"total time: {end - start}")

    return 0


def parse_command_line(args=None):

    parser = argparse.ArgumentParser(description="Run a ND simulation")
    parser.add_argument("config", help="configuration file")

    args = parser.parse_args(args=args)

    config = Config.from_file(args.config, defaults=default_config)

    return config


if __name__ == "__main__":
    main()
