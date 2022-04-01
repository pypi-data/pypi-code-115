from collections import defaultdict
from typing import Callable
from typing import List

from mold.type_dict import TypeDict
from mold.util import Singleton
from mold.util import norm_type


def norm_type_name(event: str):
    dot_idx = event.rfind('.') + 1
    return event[dot_idx:]


class EventRegistry(Singleton):
    _events: TypeDict[str, List[Callable]]

    def __init__(self):
        self._events = defaultdict(list)

    def register(self, event: type, handler: Callable):
        self._events[norm_type(event)].append(handler)

    def get_handlers(self, event: type) -> List[Callable]:
        found = self._events[event]
        if len(found) == 0:
            event = norm_type_name(event.__name__)
            found = self._events[event]

        return found


def dispatch_event(event):
    for handler in EventRegistry.get().get_handlers(type(event)):
        handler(event)
