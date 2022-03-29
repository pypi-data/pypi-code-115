import logging
import numpy as np

from typing import Optional

from pyfile_utils import Output


class State:
    def __init__(
        self,
        seed: int,
        np_random_state: np.random.RandomState,
        root: str,
        run_name: str,
        logfile: str,
        append: bool,
        screen: bool,
        verbose: str,
    ):
        logging.getLogger("matplotlib.font_manager").disabled = True
        self.seed = seed
        if np_random_state is None:
            if seed is None:
                self.np_random_state = np.random.RandomState()
            else:
                self.np_random_state = np.random.RandomState(seed=seed)
        else:
            self.np_random_state = np_random_state

        self.output_kwargs = dict(
            root=root,
            run_name=run_name,
            append=append,
            screen=screen,
            verbose=verbose,
        )
        for k, v in self.output_kwargs.items():
            setattr(self, k, v)

        self.output = Output(**self.output_kwargs)
        self.logfile = self.output.open_logfile(
            file_name=logfile, propagate=False, screen=screen
        )

    @property
    def logger(self):
        return logging.getLogger(self.logfile)
