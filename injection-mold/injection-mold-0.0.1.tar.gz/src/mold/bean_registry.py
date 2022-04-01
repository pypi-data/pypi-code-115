from typing import Callable
from typing import Set
from typing import Union

from mold.bean import BeanDefinition
from mold.util import Singleton


class BeanRegistry(Singleton):
    _beans: Set[BeanDefinition]

    def __init__(self):
        self._beans = set()

    def register(self, bean: Union[type, Callable], wrapped, ignored=None, primary=False) -> BeanDefinition:
        bean_def = BeanDefinition(bean, wrapped, ignored=ignored, primary=primary)
        self._beans.add(bean_def)
        return bean_def

    def dump(self):
        for bean in self._beans:
            print(repr(bean))

    def beans(self) -> Set[BeanDefinition]:
        return self._beans
