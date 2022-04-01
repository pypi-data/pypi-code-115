import functools
import inspect

from mold.bean_context import BeanContext
from mold.event_registry import EventRegistry
from mold.bean_registry import BeanRegistry


def resolve_deps(bean_def, kwargs):
    if BeanContext.is_valid():
        deps = BeanContext.get().resolve_deps(bean_def, kwargs)
        if deps is None:
            raise Exception(f'Unable to satisfy requirements for bean {bean_def}')
        kwargs.update(deps)

    return kwargs


def bean(ignored=None, primary=False):
    def bean_regisration_wrapper(f):

        if isinstance(f, type):
            @functools.wraps(f, updated=())
            class DepResolverCls(f):
                def __init__(self, *args, **kwargs):
                    kwargs = resolve_deps(bean_def, kwargs)
                    super().__init__(*args, **kwargs)

            dep_wrapper = DepResolverCls

        elif callable(f):
            @functools.wraps(f)
            def dep_resolver(*args, **kwargs):
                kwargs = resolve_deps(bean_def, kwargs)
                return f(*args, **kwargs)

            dep_wrapper = dep_resolver

        else:
            raise

        bean_def = BeanRegistry.get().register(f, wrapped=dep_wrapper, ignored=ignored, primary=primary)

        return dep_wrapper

    return bean_regisration_wrapper


def singleton(**kwargs):
    return bean(**kwargs)


def factory(**kwargs):
    return bean(**kwargs)


def inject(**kwargs):
    return bean(**kwargs)


def event_handler(**kwargs):
    def event_registry_wrapper(f):
        kwargs.update({'ignored': ['event']})
        injected_wrapper = bean(**kwargs)(f)

        params = inspect.signature(f).parameters
        if 'event' in params:
            event_type = params['event'].annotation
            EventRegistry.get().register(event_type, injected_wrapper)

        return injected_wrapper

    return event_registry_wrapper
