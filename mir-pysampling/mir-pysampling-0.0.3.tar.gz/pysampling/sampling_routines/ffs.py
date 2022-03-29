import numpy as np
from pysampling.sampling_routines.sampling import Sampling


class ForwardFluxSampling(Sampling):
    def __init__(self, all_xi=[0.1, 0.2, 0.5, 0.8, 0.9], n=10, **kwargs):

        Sampling.__init__(self, **kwargs)

        self.xi_initial = self.all_xi[0]
        self.xi_min = self.all_xi[1]
        self.xi_max = self.all_xi[-2]
        self.xi_final = self.all_xi[-1]

        self.tloop = None
        self.p = None
        self.niter = 0
        self.stop_arg = None
        self.time = None

    def obtain_init_configs(self):
        return Sampling.run_initial_md(self)

    def count_interval(self, hit_id):

        nhit = len(hit_id)

        assert nhit > 1, f"the number of hit {nhit} is less than 2"
        dt = (hit_id[-1] - hit_id[0]) / (nhit - 1)

        return nhit, dt

    def single_iter(self, start_configs, iter_index, prev_xi, next_xi):
        """
        run all replica and check how many encounter next_xi
        """

        logger = self.logger

        rc = self.rc

        # run dynamics
        trjs = self.engine.commitor_run(
            start_config=start_configs, suffix=f"{self.niter}"
        )

        # compute RC of the trajectories
        trjs_rc = rc.analyse_trjs(trjs)

        # find whether any of them commit to final state
        # sort trajectories based on their maximum rc value
        hit_final = 0
        maxrc = np.zeros(self.n)
        for itrj in range(self.n):
            maxrc[itrj] = np.max(trjs_rc[itrj]["rc"])
            if trjs[itrj]["n"] == 1:
                hit_final += 1
        sortid = np.argsort(maxrc)
        maxrc_batch = np.max(maxrc)
        logger.info(f"maxrc {maxrc[sortid]}")

        suc_count = 0

        keep_id = []
        for i in range(self.n):
            if maxrc[sortid[i]] > next_xi:
                keep_id.append(sortid[i])
        suc_count = len(keep_id)

        # if maximum value of rc hits final rc, stop iteration and
        # record number of trajectories that hit final state
        if (maxrc_batch >= self.xi_max) and (hit_final > 0):

            self.stop_arg = "hitting final state"
            count, _ = self.count_hit(trjs_rc=trjs_rc, xi=self.xi_max)
            suc_count = count

            if hit_final != count:
                logger.warning(
                    "warning the commitor criteria "
                    "and max xi criteria is not consistent"
                )
                logger.warning(f"hit_final = {hit_final} " f"xi_max count = {count}")

        elif (maxrc_batch >= self.xi_max) and (hit_final <= 0):

            self.stop_arg = "hitting final state with only max xi"
            count, _ = self.count_hit(trjs_rc=trjs_rc, xi=self.xi_max)
            suc_count = count
        elif (hit_final > 0) and (maxrc_batch < self.xi_max):

            self.stop_arg = "hitting final state with only commitor criteria"
            count, _ = self.count_hit(trjs_rc=trjs_rc, xi=self.xi_max)
            suc_count = hit_final
        else:
            # find new starting points based on current reaction interface
            # we can keep all the trajectories and just choose the configs
            # for which the max rc is greater than the current xi

            if suc_count > 0:
                possible_configs = self.find_restart(
                    trjs=trjs, trjs_rc=trjs_rc, keep_id=keep_id, xi=next_xi
                )

                start_configs = self.draw_config(possible_configs, replica=self.n)

            else:
                self.stop_arg = "extinction"

        rc.plot(
            f"{self.logdir}/iter{self.niter}",
            trjs,
            trjs_rc,
            [prev_xi, next_xi],
            keep_id,
        )

        return start_configs, suc_count

    def run(self, initial_configs):

        logger = self.logger

        self.stop_arg = None
        self.suc_count = []
        start_configs = initial_configs

        for i_iter in range(len(self.all_xi) - 1):

            start_configs, count = self.single_iter(
                start_configs, i_iter, self.all_xi[i_iter], self.all_xi[i_iter + 1]
            )

            self.niter = i_iter
            self.suc_count += [count]

            logger.info(
                f"{i_iter:4d} {self.all_xi[i_iter+1]:20.5g} {self.suc_count[-1]:4d}"
            )

            if self.stop_arg is not None:
                logger.error(f"stop by {self.stop_arg}")
                return 1

        self.stop_arg = "hitting maximum iterations"

        return 0

    def stats(self):

        logger = self.logger
        logger.info(f"in total {self.niter} iterations")

        if self.stop_arg == "extinction":
            logger.error("total probability is 0 (extinction)")
            logger.error("expectation of reaction time is inf (extinction)")
        else:
            self.p = 1
            for count in self.suc_count:
                self.p *= count / self.n
            self.time = (1.0 / self.p - 1.0) * self.tloop
            logger.info(f"total probability {self.p}")
            logger.info(f"expectation of reaction time {self.time}")

        return 0
