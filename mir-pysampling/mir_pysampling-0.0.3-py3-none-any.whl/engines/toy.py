"""
This is a toy n-d engine interfaced with NDSimulator

The engine call NDSimulator in with pure MD ...
"""

import numpy as np

from typing import Union

from ndsimulator.ndrun import NDRun
from pyfile_utils import Config

from .engine import Engine


class NDSimulator(Engine):
    def __init__(
        self,
        save_freq: int = 1,
        md_params: Union[dict, str] = {},
        committor_params: Union[dict, str] = {},
        **kwargs,
    ):
        """
        Args:
        """

        Engine.__init__(self, **kwargs)

        self.save_freq = save_freq

        self.md_params = (
            Config.from_file(md_params)
            if isinstance(md_params, str)
            else Config.from_dict(md_params)
        )
        self.committor_params = (
            Config.from_file(committor_params)
            if isinstance(committor_params, str)
            else Config.from_dict(committor_params)
        )
        if len(committor_params.keys()) == 0:
            self.committor_params = Config.from_dict(dict(self.md_params))

        for k in self.output_kwargs:
            self.md_params.pop(k, None)
            self.committor_params.pop(k, None)
        self.md_params.pop("run_name", None)
        self.committor_params.pop("run_name", None)

        # for config in [self.md_kwargs]:

        self.md_params.track = {"p": True, "v": True, "f": False}
        self.md_params.method = "md"
        self.md_params.steps = self.md_n_steps

        self.committor_params.method = "committor"
        self.committor_params.steps = self.committor_n_steps

    def sync_thermostat(self, config):
        config.temperature = self.temperature
        config.md_gamma = self.friction
        config.dump_freq = self.save_freq
        config.dt = self.dt
        config.pop("seed", 0)
        config.pop("random", 0)
        config.pop("run_name", 0)

    def check_instance(self):
        pass

    def single_run(self, config, kwargs: dict, root: str, run_name: str):

        assert root[0] != "/"

        sim = NDRun(
            random=self.np_random_state,
            root=self.output_kwargs["root"]
            + "/"
            + self.output_kwargs["run_name"]
            + "/"
            + root,
            run_name=run_name,
            append=self.output_kwargs["append"],
            screen=False,
            verbose=self.output_kwargs["verbose"],
            **kwargs,
        )
        sim.modify.set_positions(config["x"])
        v = config.get("v", None)
        if v is not None:
            sim.modify.set_velocity(v=v)
        sim.begin()
        sim.run()
        sim.end()
        trj = {
            "x": np.array(sim.stat.positions),
            "v": np.array(sim.stat.velocities),
        }
        trj["n"] = np.ones(trj["x"].shape[0], dtype=int) * int(
            getattr(sim, "commit_basin", -1)
        )
        return trj

    def single_md_run(self, config, root, run_name):
        self.sync_thermostat(self.md_params)
        return self.single_run(config, self.md_params, root, run_name)

    def single_committor_run(self, config, root, run_name):
        self.sync_thermostat(self.committor_params)
        return self.single_run(config, self.committor_params, root, run_name)

    def obtain_config(self, trj, iconfig):
        return {"x": trj["x"][iconfig], "v": trj["v"][iconfig]}

    def clean_data(self):
        pass

    def get_structure(self, config):
        x0 = config.get("x0", None)
        v0 = config.get("v0", None)
        return {"x": x0, "v": v0}