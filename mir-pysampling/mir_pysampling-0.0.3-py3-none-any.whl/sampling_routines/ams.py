import numpy as np
from pysampling.sampling_routines.sampling import Sampling


class AdaptiveMultilevelSplitting(Sampling):
    def __init__(
        self,
        xi_initial=None,
        xi_min=None,
        xi_max=None,
        xi_final=None,
        n=10,
        k=5,
        instance_name="default_ams",
        **kwargs,
    ):

        Sampling.__init__(self, **kwargs)

        self.tloop = None
        self.p = None
        self.niter = 0
        self.stop_arg = None
        self.all_xi = []

        # sanity check
        assert self.n > 0, "total number of replica has to be bigger than 0"
        assert self.n > self.k, (
            "total number of replica has to be bigger"
            "than the number of killing replica"
        )
        assert self.max_iter > 0, "maximum iterations need to be larger than 0"

    def obtain_init_configs(self):
        return Sampling.run_initial_md(self)

    def count_interval(self, hit_id):

        nhit = len(hit_id)

        assert nhit >= 1, f"the number of hit {nhit} is less than 2"
        dt = (hit_id[-1] - hit_id[0]) / (nhit - 1)

        return nhit, dt

    def single_iter(self, start_configs, prev_kill_lev):

        logger = self.logger

        rc = self.rc

        trjs = self.engine.commitor_run(
            start_config=start_configs, suffix=f"{self.niter}"
        )

        # compute RC of the trajectories
        trjs_rc = rc.analyse_trjs(trjs)

        # # find whether any of them commit to final state
        # # sort trajectories based on their maximum rc value
        # hit_final = 0
        # for itrj in range(self.n):
        #     maxrc[itrj] = np.max(trjs_rc[itrj]["rc"])
        #     if trjs[itrj]["n"] == 1:
        #         hit_final += 1
        maxrc = np.zeros(self.n)
        sortid = np.argsort(maxrc)
        maxrc_batch = np.max(maxrc)
        logger.info(f"maxrc {maxrc[sortid]}")

        kill_lev = float("Inf")
        keep_id = None
        self.stop_arg = None
        suc_count = 0

        # if the maximum rc hit the final rc. stop the iteration
        # and record the number of replica hit the final state
        #         if (maxrc_batch >= self.xi_max) and (hit_final > 0):
        #
        #             self.stop_arg = "hitting final state"
        #             count, _ = self.count_hit(trjs_rc=trjs_rc, xi=self.xi_max)
        #             suc_count = count
        #             kill_lev = self.xi_max
        #
        #             if hit_final != count:
        #                 logger.warning(
        #                     "warning the commitor criteria "
        #                     "and max xi criteria is not consistent"
        #                 )
        #                 logger.warning(f"hit_final = {hit_final} " f"xi_max count = {count}")
        #
        if maxrc_batch >= self.xi_max:

            self.stop_arg = "hitting final state with only max xi"
            count, _ = self.count_hit(trjs_rc=trjs_rc, xi=self.xi_max)
            suc_count = count
            kill_lev = self.xi_max

        # elif (hit_final > 0) and (maxrc_batch < self.xi_max):

        #     self.stop_arg = "hitting final state with only commitor criteria"
        #     count, _ = self.count_hit(trjs_rc=trjs_rc, xi=self.xi_max)
        #     suc_count = hit_final
        #     kill_lev = np.max(maxrc)
        else:
            # determine killing levels
            kill_lev = maxrc[sortid[self.k - 1]]

            if kill_lev < prev_kill_lev:
                # self.stop_arg = "backward progress"
                sorted_maxrc = maxrc[sortid]
                ind0 = np.where(sorted_maxrc > prev_kill_lev)[0]
                if len(ind0) > 0:
                    kill_lev = sorted_maxrc[ind0[0]]
                else:
                    kill_lev = float("Inf")
                    self.stop_arg = "extinction"
                    suc_count = 0

            if maxrc[sortid[-1]] <= kill_lev:
                kill_lev = float("Inf")
                self.stop_arg = "extinction"
                suc_count = 0
            else:
                current_k = self.k
                for idx in range(current_k, self.n):
                    if maxrc[sortid[idx]] <= kill_lev:
                        current_k = idx + 1
                suc_count = self.n - current_k

                keep_id = sortid[current_k:]

                # find new starting points
                possible_configs = self.find_restart(
                    trjs=trjs, trjs_rc=trjs_rc, keep_id=keep_id, xi=kill_lev
                )

                start_configs = self.draw_config(possible_configs, replica=self.n)

        rc.plot(
            f"{self.logdir}/iter{self.niter}",
            trjs,
            trjs_rc,
            [prev_kill_lev, kill_lev],
            keep_id,
        )

        self.all_xi.append(kill_lev)

        return start_configs, suc_count, kill_lev

    def run(self, initial_configs):

        # run AMS iterations

        logger = self.logger

        self.niter = 0
        self.stop_arg = None
        self.suc_count = []
        kill_levs = [self.xi_min]
        start_configs = initial_configs

        while self.stop_arg is None:

            start_configs, count, kill_lev = self.single_iter(
                start_configs, kill_levs[-1]
            )

            kill_levs += [kill_lev]
            self.suc_count += [count]

            if (self.niter >= self.max_iter) and (self.stop_arg is None):
                self.stop_arg = "hitting maximum iterations"

            logger.info(f"{self.niter:4d} {kill_lev:20.5g} {count:4d}")

            self.niter += 1

        logger.info(f"stop by {self.stop_arg}")

        return 0

    def stats(self):

        logger = self.logger
        logger.info(f"in total {self.niter} iterations")
        if "extinction" in self.stop_arg:
            logger.error("total probability is 0")
        else:
            self.p = 1
            for count in self.suc_count:
                self.p *= count / self.n
            self.time = (1.0 / self.p - 1.0) * self.tloop
            logger.info(f"total probability {self.p}")
            logger.info(f"expectation of reaction time {self.time}")

        return 0
