import numpy as np

from .sampling import (
    Sampling,
    combine_trjs,
    print_trj,
    print_header,
)

"""
with 1D reaction coordinate
"""


class TransitionPathSampling(Sampling):
    """_summary_

    Args:
        max_iter (int, optional): . Defaults to 100.
        all_basins (list, optional): . Defaults to [0, 1],
        all_basins (list, optional): . Defaults to [].
        start_trj (dict, optional): . Defaults to None.
        t_max (float, optional): . Defaults to 25.
        k (float, optional): . Defaults to 0.01.
    """

    def __init__(
        self,
        all_basins: list = [0, 1],
        start_trj=None,
        start_trj_name: str = None,
        t_max: float = 25,
        k: float = 0.01,
        **kwargs,
    ):

        Sampling.__init__(self, **kwargs)

        self.all_basins = all_basins

        self.start_trj = start_trj
        self.start_trj_name = start_trj_name
        self.t_max = t_max
        self.k = k

        self.accept = 0
        self.reject = 0
        self.niter = 0
        self.stop_arg = None

        # calculate pdf and cdf for oneway shooting
        self.t_list = np.arange(-self.t_max, self.t_max + 1, 1, dtype=np.int)
        pdf_t = np.exp(self.k * self.t_list)
        pdf_t = pdf_t / np.sum(pdf_t)
        self.cdf_t = np.array([np.sum(pdf_t[:i]) for i in range(pdf_t.shape[0])])

    def obtain_init_configs(self):

        if self.start_trj is None:
            return self.load_initial(self.start_trj_name)
        else:
            return self.start_trj

    def load_initial(self, filename):

        data = dict(np.load(filename, allow_pickle=True))

        x = data.pop("x", data.pop("pos", None))
        v = data.pop("v", data.pop("vel", None))
        n = data.pop("n", data.pop("label", None))

        self.sp_index = data.pop("sp_index", -1)
        if self.sp_index == -1:
            raise RuntimeError("initial data does not contain sp_index")

        if x is None:
            raise RuntimeError("npz file should contain pos array")

        self.start_config = {"x": x, "v": v, "n": n}
        for k in data:
            self.start_config[k] = data[k]

        self.n_configs = x.shape[0]

        # if "pe" in data:
        # self.sp_index = np.argmax(data["pe"]) if sp_index == -1 else sp_index

        if n is not None:
            basin0 = n[0]
            basin1 = n[-1]
            self.logger.info(
                f"override the original all_basins set up from {self.all_basins} to [{basin0}, {basin1}]"
            )
            self.all_basins = [basin0, basin1]

        self.sp_index = self.n_configs // 2 if self.sp_index == -1 else self.sp_index

        return self.start_config

    def run(self, starting_configs):

        logger = self.logger

        self.accept = 0
        self.reject = 0
        direction = {-1: "bwd", 1: "fwd"}

        curr_trj = starting_configs
        n_full_path = 0
        for self.niter in range(self.max_iter):

            attempt_dir, sp_index = self.shooting_point(self.sp_index, self.n_configs)
            sp_config = self.engine.obtain_config(curr_trj, sp_index)

            if sp_config["v"] is not None:
                sp_config["v"] *= attempt_dir

            target_basin = self.all_basins[(attempt_dir + 1) // 2]

            trial_trj = self.engine.committor_run(
                start_config=[sp_config], suffix=f"{self.niter}", force_restart=True
            )
            trial_trj = trial_trj[0]

            if self.niter == 0:
                header = "#"
                for h in ["niter", "dir", "tgt", "sp", "tot."]:
                    header += f" {h:>5s}"
                header += print_header(trial_trj)

            prints = f"  {self.niter:>5d} {direction[attempt_dir]:>5s} {target_basin:>5d} {sp_index:>5d} {self.n_configs:>5d} "
            prints += print_trj(trial_trj)

            cond1 = trial_trj["n"][-1] == target_basin
            cond2 = True

            if cond1 and cond2:
                result = "accept"
                self.accept += 1
                self.sp_index, curr_trj = combine_trjs(
                    (attempt_dir + 1) // 2, sp_index, curr_trj, trial_trj
                )
                self.n_configs = curr_trj["x"].shape[0]
                np.savez(
                    f"{self.root}/{self.run_name}/{n_full_path}_path.npz",
                    **curr_trj,
                    sp_index=self.sp_index,
                )
                n_full_path += 1
            else:
                result = "reject"
                self.reject += 1
                # rc.plot(f"{self.root}/{self.run_name}/iter{self.niter}", trjs, trjs_rc,
                #         [prev_kill_lev, kill_lev], keep_id)

            if self.niter == 0:
                logger.info(header + f" result")
            logger.info(prints + f" {result}")
            np.savez(
                f"{self.root}/{self.run_name}/{self.niter}-{result}.npz", **trial_trj
            )

    def shooting_point(self, original_sp, nconfig):

        if nconfig < 2 * self.t_max:
            raise RuntimeError("the path is too short now")

        attempt_dir = self.np_random_state.choice([1, -1])
        accept = False
        while accept is False:

            # determin dtao
            r2 = self.np_random_state.rand()
            idk = np.argmin(np.abs(self.cdf_t - r2))
            if r2 > self.cdf_t[idk]:
                tao = self.t_list[idk]
            elif (idk + 1) < len(self.t_list):
                tao = self.t_list[idk + 1]
            else:
                tao = self.t_list[-1]

            tao = attempt_dir * tao

            iconfig = original_sp + tao
            if iconfig >= nconfig or iconfig < 0:
                accept = False
            else:
                accept = True

        return attempt_dir, iconfig

    def stats(self):

        logger = self.logger
        logger.info(f"in total {self.niter} iterations")
        logger.info(f"acceptance ratio {self.accept/self.niter}")

        return 0

    # def assemble_path(self, starting_config, max_iter):
    #     """
    #     run with MD simulation started from given position and +- of the given velocities.
    #     if + and - v ended at different basins, accept and return the join trajectories

    #     start_config {'x':[n*3],'v':[n*3]}
    #     """

    #     logger = self.logger

    #     x = starting_config["x"]
    #     v = starting_config["v"]
    #     x0 = starting_config["x"]
    #     v0 = starting_config["v"]

    #     for id_iter in range(max_iter):

    #         trial = []
    #         n = []
    #         for idx in range(2):
    #             self.engine.xyz_prefix = f"assm_pth_{id_iter}_{idx}"
    #             trial += [
    #                 self.engine.committor_run(
    #                     start_config=[{"x": x, "v": v * (idx * 2 - 1)}],
    #                     suffix=f"{id_iter}_{idx}",
    #                 )[0]
    #             ]
    #             n += [trial[-1]["n"]]

    #         sp, join_trj = combine_trjs(0, 0, trial[1], trial[0])
    #         np.savez(f"assm_pth_{id_iter}.npz", **join_trj)

    #         nconfig = len(join_trj["x"])

    #         prints = f"ass. {id_iter:5d} {n[0]:3d} {n[1]:3d}" f" len {nconfig:4d}"

    #         if "alle" in join_trj:
    #             alle = join_trj["alle"]
    #             prints += (
    #                 f" Temp {np.min(alle[:, 0]):4.0f}"
    #                 f" to {np.max(alle[:, 0]):4.0f}"
    #                 f" max_pe {np.max(alle[:, 1]):8.2f},"
    #                 f" min_pe {np.min(alle[:, 1]):8.2f},"
    #                 f" Et {alle[0, 3]:6.2f} to {alle[-1, 3]:6.2f}"
    #             )
    #         logger.info(prints)

    #         cond1 = n[0] != n[1]
    #         cond2 = (n[0] in self.all_basins) and (n[1] in self.all_basins)

    #         if cond1 and cond2:
    #             if n[0] == self.all_basins[0]:
    #                 return join_trj
    #             else:
    #                 return flip_trj(join_trj)
    #         else:
    #             result = "reject"

    #         x, v = x0, v0

    #     return join_trj
