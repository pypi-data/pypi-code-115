from typing import Callable, Optional, TypeVar, Any
from django.core.cache import cache

_T = TypeVar('_T')

class memcached_function:
    cache_key = None
    cache_expires = None

    def __init__(
        self, 
        cache_key: Callable[..., _T],
        func: Callable[..., _T] = None,
        cache_expires: Optional[int] = None,
    ):
        self.cache_key = cache_key
        self.func = func
        self.cache_expires = cache_expires
        self.__doc__ = getattr(func, '__doc__')

    def __call__(self, func, *args: Any, **kwds: Any) -> Any:
        self.func = func
        def wrapper(instance):
            return self.__get__(instance)
        return wrapper

    def __get__(self, instance, cls=None) -> Any:
        if instance is None:
            return self
        if not isinstance(self.cache_key, str):
            self.cache_key = getattr(
                instance, self.cache_key.__name__)()
        cache_value = cache.get(self.cache_key)
        if cache_value:
            return cache_value
        cache_value = self.func(instance)
        cache.set(
            key=self.cache_key,
            value=cache_value,
            timeout=self.cache_expires)
        return cache_value