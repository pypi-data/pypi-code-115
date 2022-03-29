import logging
import numpy as np
import pickle

from typing import Optional
from pyfile_utils import save_file

from pysampling.engines import engine_from_config
from pysampling.colvars import colvar_from_config
from pysampling.state import State


class Sampling(State):
    def __init__(
        self,
        seed: Optional[int] = None,
        np_random_state: Optional[np.random.RandomState] = None,
        root: str = "./",
        run_name: str = "sampling",
        logfile: str = "log",
        append: bool = False,
        screen: bool = True,
        verbose: str = "info",
        engine_name: str = "NDSimulator",
        rc_name: str = "Original",
        engine=None,
        engine_param=None,
        rc=None,
        rc_param=None,
        max_iter: int = 100,
        **kwargs,
    ):
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
        self.max_iter = max_iter

        if engine_param is None:
            self.engine_param = {
                k: v for k, v in kwargs.items() if k not in self.output_kwargs
            }
            engine_param = {}
        else:
            self.engine_param = {
                k: v for k, v in engine_param.items() if k not in self.output_kwargs
            }

        if rc_param is None:
            self.rc_param = {
                k: v for k, v in kwargs.items() if k not in self.output_kwargs
            }
            rc_param = {}
        else:
            self.rc_param = {
                k: v for k, v in rc_param.items() if k not in self.output_kwargs
            }

        sub_root = self.root + "/" + self.run_name + "/"

        for k, v in self.output_kwargs.items():
            self.engine_param[k] = v
            self.rc_param[k] = v

        # generate MD/MC engine
        self.engine_param["seed"] = seed
        self.engine_param["np_random_state"] = self.np_random_state
        self.engine_param["root"] = sub_root + engine_param.pop("root", ".")
        self.engine_param["engine_name"] = engine_name
        self.engine_param["run_name"] = "engine_workdir"
        self.engine = (
            engine_from_config(self.engine_param) if engine is None else engine
        )

        self.rc_param["seed"] = seed
        self.rc_param["np_random_state"] = self.np_random_state
        self.rc_param["root"] = sub_root + rc_param.pop("root", ".")
        self.rc_param["colvar_name"] = rc_name
        self.rc_param["run_name"] = "rc_workdir"
        self.rc = colvar_from_config(self.rc_param) if rc is None else rc

    @property
    def logger(self):
        return logging.getLogger(self.logfile)

    def draw_config(self, hit_config, replica):

        nhit = len(hit_config)

        if replica > nhit:
            draw_max = int(np.ceil(replica / nhit) * nhit)
        elif replica == nhit:
            return hit_config
        else:
            draw_max = nhit

        draw_id = self.np_random_state.randint(0, draw_max - 1, replica)
        start_configs = []
        for i in range(len(draw_id)):
            iconfig = draw_id[i]
            if iconfig >= nhit:
                iconfig = iconfig % nhit
            start_configs += [hit_config[iconfig]]

        return start_configs

    def obtain_init_configs(self):
        raise NotImplementedError

    def run_initial_md(self):
        logger = self.logger

        rc = self.rc

        initial_trj = self.engine.mdrun(start_config=[{"x": self.initial}])

        # store N configurations that hit the initial RC iso-surface
        trjs_rc = rc.analyse_trjs(initial_trj)
        rc.plot(
            f"{self.root}/{self.run_name}/md",
            initial_trj,
            trjs_rc,
            [self.xi_min, self.xi_initial],
            None,
        )

        hit_configs, hit_id = self.find_hit(
            initial_trj[0], trjs_rc[0], self.xi_min, self.xi_initial
        )
        logger.debug(f"hit_id {hit_id}")

        start_configs = self.draw_config(hit_configs, self.n)
        self.nhit, self.tloop = self.count_interval(hit_id)

        logger.info(f"nhit {self.nhit} t_loop {self.tloop:.8f}")
        return start_configs

    def count_hit(self, trjs_rc, xi):
        nhit = 0
        id_list = []
        for i, trj_rc in enumerate(trjs_rc):
            if np.max(trj_rc["rc"]) >= xi:
                id_list += [i]
                nhit += 1
        return nhit, id_list

    def find_restart(self, trjs, trjs_rc, keep_id, xi):
        """

        Args:
            trjs (list): list of trajectories
            trjs_rc (list): list of reaction coordinates
            keep_id (list): list of trajectory indices to check
            xi (float): the level to check
        """

        logger = self.logger
        hit_config = []
        for i in keep_id:
            trj = trjs[i]
            trj_rc = trjs_rc[i]

            l = len(trj_rc["rc"])
            iconfig = 0
            found = False
            while iconfig < l and not found:
                if trj_rc["rc"][iconfig] >= xi:
                    hit_config += [self.engine.obtain_config(trj, iconfig)]
                    found = True
                iconfig += 1
            if not found:
                iconfig = np.argmax(trj_rc["rc"])
                logger.info(f"maximum rc of {iconfig} {trj_rc['rc'][iconfig]} < {xi}")
                hit_config += [self.engine.obtain_config(trj, iconfig)]
                found = True
            assert found, "the keep trajectory cannot find" " the hitting point"
        self.engine.clean_data()
        return hit_config

    def find_hit(self, trj, trj_rc, xi_min, xi_initial):
        hit_config = []
        hit_id = []
        from_initial = True
        for i in range(1, len(trj_rc["rc"])):
            if trj_rc["rc"][i] >= xi_min and (from_initial is True):
                hit_id += [i]
                hit_config += [self.engine.obtain_config(trj, i)]
                from_initial = False
            elif trj_rc["rc"][i] <= xi_initial and (from_initial is False):
                from_initial = True
        self.engine.clean_data()

        return hit_config, hit_id

    @staticmethod
    def save_sampler(sampler):
        save_file(
            item=sampler,
            filename=f"{sampler.root}/{sampler.run_name}.pickle",
            supported_formats={"pickle": "pickle"},
        )

    @staticmethod
    def load_sampler(sampler_filename):
        with open(sampler_filename, "rb") as f:

            sampler = pickle.load(f)

        return sampler


def flip_trj(old_trj):
    """
    flip the trajectory and reverse its velocities
    """

    new_trj = {}
    for k in old_trj:
        new_trj[k] = np.flip(new_trj[k], axis=0)
    new_trj["v"] = -new_trj["v"]

    return new_trj


def combine_trjs(s, sp_index, old_trj, new_trj):
    """
    if s == 0
        join flip(new_trj[1:]) to old_trj[sp_index:]
    else:
        join old_trj[:sp_index+1] to new_trj[1:]
    """

    new_data = {}
    if s == 1:
        for k, v in new_trj.items():
            if type(v) != type(old_trj[k]):
                if isinstance(old_trj[k], (list, np.ndarray)) and isinstance(
                    v, (int, float, bool)
                ):
                    new_data[k] = np.hstack([old_trj[k][0], v])
                else:
                    raise ValueError(f"type is wrong for {k} {v} vs {old_trj[k]}")
            elif isinstance(v, (int, float, bool)):
                new_data[k] = np.hstack([old_trj[k], v])
            else:
                if len(old_trj[k].shape) == 1:
                    new_data[k] = np.hstack([old_trj[k][: sp_index + 1], v[1:]])
                else:
                    new_data[k] = np.vstack([old_trj[k][: sp_index + 1], v[1:]])
        new_sp_index = sp_index
    else:
        for k, v in new_trj.items():
            if type(v) != type(old_trj[k]):
                if isinstance(old_trj[k], (list, np.ndarray)) and isinstance(
                    v, (int, float, bool)
                ):
                    new_data[k] = np.hstack([v, old_trj[k][1]])
                else:
                    raise ValueError(f"type is wrong for {k} {v} vs {old_trj[k]}")
            elif isinstance(v, (int, float, bool, str)):
                new_data[k] = np.hstack([v, old_trj[k]])
            else:
                # print(k)
                # for arr in [new_trj[k], old_trj[k]]:
                #     try:
                #         print(arr.shape)
                #     except:
                #         print(len(arr), arr[0])
                if len(old_trj[k].shape) == 1:
                    new_data[k] = np.hstack(
                        [np.flip(v[1:], axis=0), old_trj[k][sp_index:]]
                    )
                else:
                    new_data[k] = np.vstack(
                        [np.flip(v[1:], axis=0), old_trj[k][sp_index:]]
                    )
        new_data["v"] = -new_data["v"]
        new_sp_index = len(new_trj["v"]) - 1

    return new_sp_index, new_data


def print_trj(trial_trj):
    prints = ""
    x = trial_trj["x"]
    prints = f" {len(x):>6d}"
    if "n" in trial_trj:
        n = trial_trj["n"]
        if isinstance(n, int):
            prints += f" {n:>4d}"
        else:
            prints += f" {n[0]:>4d} {n[-1]:>4d}"
    if "sp_index" in trial_trj:
        sp = trial_trj["sp_index"]
        prints += f" {sp:8d}"
    if "T" in trial_trj:
        T = trial_trj["T"]
        prints += f" {np.min(T):4.0f} {np.max(T):4.0f}"
    if "pe" in trial_trj:
        pe = trial_trj["pe"]
        prints += f" {np.min(pe):10.2f} {np.max(pe):10.2f}"
    if "etotal" in trial_trj:
        alle = trial_trj["etotal"]
        prints += f" {alle[0]:6.2f} {alle[-1]:6.2f}"
    if "intc" in trial_trj:
        intc0 = trial_trj["intc"][0, -1]
        intc1 = trial_trj["intc"][-1, -1]
        prints += f" {intc0:6.2g} {intc1:6.2g}"
    return prints


def print_header(trial_trj):
    prints = ""
    s = "len(x)"
    prints = f" {s:>6s}"
    if "n" in trial_trj:
        if isinstance(trial_trj["n"], int):
            n = "n"
            prints += f" {n:>4s}"
        else:
            n = ["n0", "n1"]
            prints += f" {n[0]:>4s} {n[-1]:>4s}"
    if "sp_index" in trial_trj:
        prints += f" sp_index"
    if "T" in trial_trj:
        prints += f" Tmin Tmax"
    if "pe" in trial_trj:
        Emin = "Emin"
        Emax = "Emax"
        prints += f" {Emin:>10s} {Emax:>10s}"
    if "etotal" in trial_trj:
        Et0 = "Et0"
        Et1 = "Et1"
        prints += f" {Et0:>6s} {Et1:>6s}"
    if "intc" in trial_trj:
        intc0 = "intc0"
        intc1 = "intc1"
        prints += f" {intc0:>6s} {intc1:>6s}"
    return prints
