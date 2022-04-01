from dataclasses import dataclass

from mold import BeanContext
from mold import dispatch_event
from mold import event_handler


@dataclass
class FooEvent:
    message: str


def test_single_handler():
    handler_1_called = False

    @event_handler()
    def handler_1(event: FooEvent):
        nonlocal handler_1_called
        handler_1_called = True
        assert event.message == 'test'

    with BeanContext():
        dispatch_event(FooEvent('test'))
        assert handler_1_called


def test_multiple_handlers():
    handler_1_called = False
    handler_2_called = False

    @event_handler()
    def handler_1(event: FooEvent):
        nonlocal handler_1_called
        handler_1_called = True
        assert event.message == 'test'

    @event_handler()
    def handler_2(event: FooEvent):
        nonlocal handler_2_called
        handler_2_called = True
        assert event.message == 'test'

    with BeanContext():
        dispatch_event(FooEvent('test'))
        assert handler_1_called
        assert handler_2_called
