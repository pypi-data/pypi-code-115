import numpy as np

from pysampling.sampling_routines.sampling import (
    Sampling,
    combine_trjs,
    print_trj,
    print_header,
)


class CommittorAnalysis(Sampling):
    def __init__(self, **kwargs):

        Sampling.__init__(self, **kwargs)
        self.x0 = self.engine.get_structure(kwargs)

    def obtain_init_configs(self):
        return [self.x0]

    def run(self, starting_configs):
        """
        run with MD simulation started from given position and +- of the given velocities.
        if + and - v ended at different basins, accept and return the join trajectories

        start_config {'x':[n*3],'v':[n*3]}
        """

        logger = self.logger

        self.counter = {}

        for id_config, config in enumerate(starting_configs):

            self.counter[id_config] = {}

            for id_iter in range(self.max_iter):

                x = config["x"]

                v = config.get("v", None)
                if v is None and hasattr(self.engine, "initialize_v"):
                    v = self.engine.initialize_v()

                # self.engine. = f"assm_pth_{id_config}_{id_iter}"

                if v is not None:
                    trial = self.engine.committor_run(
                        start_config={
                            "fwd": {"x": x, "v": v},
                            "bwd": {"x": x, "v": -v},
                        },
                        suffix=f"{id_config}_{id_iter}",
                        force_restart=True,
                    )
                else:
                    trial = self.engine.committor_run(
                        start_config=[{"x": x}],
                        suffix=f"{id_config}_{id_iter}_fwd",
                        force_restart=True,
                    )

                    struct = self.engine.obtain_config(trial[-1], 0)
                    struct["v"] = -struct["v"]
                    trial += [
                        self.engine.committor_run(
                            start_config=[struct],
                            suffix=f"{id_config}_{id_iter}_bwd",
                            force_restart=True,
                        )[0]
                    ]

                for t in trial:
                    basin = t["n"][-1]
                    if basin not in self.counter[id_config]:
                        self.counter[id_config][basin] = 0
                    self.counter[id_config][basin] += 1

                sp, join_trj = combine_trjs(
                    s=0, sp_index=0, old_trj=trial[0], new_trj=trial[1]
                )
                join_trj["sp_index"] = sp
                np.savez(
                    f"{self.root}/{self.run_name}/joint_{id_iter}.npz",
                    **join_trj,
                )

                prints = f"  {id_iter:5d} " + print_trj(join_trj)

                if id_iter == 0:
                    header = "#"
                    for h in ["niter"]:
                        header += f" {h:5s} "
                    header += print_header(join_trj)
                    logger.info(header)

                logger.info(prints)
                del trial

    def stats(self):
        pass
