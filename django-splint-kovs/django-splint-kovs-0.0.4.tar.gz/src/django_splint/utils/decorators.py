from typing import Callable, Optional, TypeVar, Any
from django.core.cache import cache

_T = TypeVar('_T')

class splint_cached_property:
    def __init__(
        self,
        func: Callable[..., _T],
        cache_key_function: Callable[..., _T] = None,
        cache_expires: Optional[int] = None,
    ):
        """_summary_

        Args:
            cache_key_function (Callable[..., _T]): Callable should be return a sha str.
            func (Callable[..., _T], optional): Callable should be return any 
                picklable Python object. 
                Defaults to None when this class is used as decorator.
            cache_expires (Optional[int], optional): The timeout argument is 
                optional and defaults to the timeout argument of the appropriate 
                backend in the CACHES setting. 
                Its the number of seconds the value should be stored in the cache. 
                A timeout of 0 wont cache the value. 
                Defaults to None for timeout will cache the value forever..

        Returns:
            Picklable: picklable Python object loaded.
        """
        self.func = func
        self.cache_key_function = cache_key_function
        self.attrname = None
        self.cache_expires = cache_expires
        self.__doc__ = getattr(func, '__doc__')

    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same cached_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def __get__(self, instance, cls=None) -> Any:
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it.")
        if self.cache_key_function is None:
            try:
                cache_key = getattr(
                    instance, 'get_cache_key')()
            except AttributeError:
                msg = (
                    "No 'get_cache_key' attribute on instance to cache "
                    f"{self.attrname!r} property."
                )
                raise TypeError(msg) from None
        else:
            cache_key = self.cache_key_function(instance)
        if not isinstance(cache_key, str):
            raise TypeError(
                f'{self.cache_key_function.__name__} must be return a sha str')    
        cache_value = cache.get(cache_key)
        if cache_value:
            return cache_value
        cache_value = self.func(instance)
        cache.set(
            key=cache_key,
            value=cache_value,
            timeout=self.cache_expires)
        return cache_value