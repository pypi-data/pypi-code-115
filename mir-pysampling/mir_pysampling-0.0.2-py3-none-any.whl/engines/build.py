from pyfile_utils import instantiate, load_callable

from .engine import Engine


def engine_from_config(config):
    """build a engine class with given string name that matches
    the engine class namd.

    Args:

    config: dictionary that may contain keywords for the engine
    """

    engine_name = config.get("engine_name")
    try:
        engine_class = load_callable(engine_name)
    except:
        if isinstance(engine_name, str):
            engine_class = load_callable("pysampling.engines." + engine_name)
        else:
            raise ValueError("cannot load the engine name")

    # because most engine instance has the kwargs sign
    _, kwargs_child = instantiate(
        engine_class,
        all_args=config,
        return_args_only=True,
    )
    _, kwargs_base = instantiate(
        Engine,
        all_args=config,
        return_args_only=True,
    )
    return engine_class(**{**kwargs_child, **kwargs_base})
