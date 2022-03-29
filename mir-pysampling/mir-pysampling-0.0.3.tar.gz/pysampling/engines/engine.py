#
"""

Base class for all engines


Logging behavior:

   logger is set to pipe to stdout and a file {logdir}/{logger_name}.log

   available attrs to be set: logdir, logger_name, log_freq
   available attrs to be used: logger, log_freq

"""
import numpy as np
from typing import Optional, Union

from pyfile_utils import Output

from pysampling.state import State


class Engine(State):
    def __init__(
        self,
        temperature: float,
        friction: float,
        dump_freq: int,
        dt: float,
        steps: int = -1,
        md_n_steps: int = -1,
        committor_n_steps: int = -1,
        seed: Optional[int] = None,
        np_random_state: Optional[np.random.RandomState] = None,
        root: str = "./",
        run_name: str = "engine_workdir",
        logfile: str = "log",
        append: bool = False,
        screen: bool = True,
        verbose: str = "info",
        x0: str = None,
        entries: list = ["x", "v"],
        **kwargs,
    ):
        self.temperature = temperature
        self.steps = steps
        self.committor_n_steps = (
            self.steps if committor_n_steps < 0 else committor_n_steps
        )
        self.md_n_steps = self.steps if md_n_steps < 0 else md_n_steps
        self.friction = friction
        self.dump_freq = dump_freq
        self.dt = dt
        self.x0 = x0
        self.entries = entries

        State.__init__(
            self,
            seed=seed,
            np_random_state=np_random_state,
            root=root,
            run_name=run_name,
            logfile=logfile,
            append=append,
            screen=screen,
            verbose=verbose,
        )
    
    def get_replica_log(self, root, run_name):
        return Output(root=root, run_name=run_name, append=self.append, screen=self.screen, verbose=self.verbose)

    def run_langevin(self, name, config, n_steps):
        raise NotImplementedError("run_langevin is not implemented")

    def multiple_runs(
        self, run_function: callable, start_config: Union[dict, list], suffix="md"
    ):

        assert isinstance(start_config, (dict, list)), (
            f"starting config has to be a list," f"but it is a {type(start_config)}"
        )

        if isinstance(start_config, list):
            if len(start_config) > 1:
                iterator = enumerate(start_config)
            else:
                iterator = {"": start_config[0]}.items()
        else:
            iterator = start_config.items()

        trjs = []
        for prefix, configuration in iterator:
            root = configuration.pop("root", "./")
            if prefix == "":
                run_name = suffix
                local_root = root
            else:
                # some bugs here in the file name. be careful
                run_name = str(prefix)
                local_root = root + "/" + suffix
            trjs.append(
                run_function(
                    self, config=configuration, root=local_root, run_name=run_name
                )
            )
        return trjs
    
    def single_md_run(self):
        raise NotImplementedError

    def md_run(self, start_config=[], suffix="md", force_restart=True):
        return self.multiple_runs(
            run_function=type(self).single_md_run,
            start_config=start_config,
            suffix=suffix,
        )

    def committor_run(self, start_config=[], suffix="", force_restart=True):
        return self.multiple_runs(
            run_function=type(self).single_committor_run,
            start_config=start_config,
            suffix=suffix,
        )

    def get_structure(self, config):
        raise NotImplementedError
