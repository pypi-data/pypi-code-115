from pyfile_utils import instantiate, load_callable

from .base import Colvar


def colvar_from_config(config):
    """build a engine class with given string name that matches
    the engine class namd.

    Args:

    config: dictionary that may contain keywords for the engine
    """

    colvar_name = config.get("colvar_name")
    try:
        colvar_class = load_callable(colvar_name)
    except:
        if isinstance(colvar_name, str):
            colvar_class = load_callable("pysampling.colvars." + colvar_name)
        else:
            raise ValueError(f"cannot load the colvar name {colvar_name}")

    # because most engine instance has the kwargs sign
    _, kwargs_child = instantiate(
        colvar_class,
        all_args=config,
        return_args_only=True,
    )
    _, kwargs_base = instantiate(
        Colvar,
        all_args=config,
        return_args_only=True,
    )

    return colvar_class(**{**kwargs_child, **kwargs_base})
