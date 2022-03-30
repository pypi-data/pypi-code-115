from time import perf_counter
from contextlib import contextmanager
import logging.config


logger = logging.getLogger("entityscan")
logger.setLevel("INFO")


@contextmanager
def timelog(msg: str, level=logging.INFO):
    pc = perf_counter()
    logger.log(msg=f"Start: {msg}", level=level)
    yield
    logger.log(msg=f"Done : {msg} [{perf_counter() - pc:.2f}s]", level=level)
