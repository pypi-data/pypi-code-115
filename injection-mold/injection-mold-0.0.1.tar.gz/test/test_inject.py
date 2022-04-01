from demo.order_repo import OrderRepo
from mold import BeanContext
from mold import BeanRegistry
from mold import factory
from mold import inject
from mold import singleton


def test_clean_registry():
    assert len(BeanRegistry.get().beans()) == 0


def test_inject_simple_func(demo_beans):
    @inject()
    def sample_inject_fn(order_repo: OrderRepo):
        return isinstance(order_repo, OrderRepo)

    with BeanContext():
        assert sample_inject_fn()


def test_inject_simple_class(demo_beans):
    @inject()
    class SimpleInjectCls:
        def __init__(self, order_repo: OrderRepo):
            self.order_repo = order_repo

    with BeanContext():
        cls = SimpleInjectCls()
        assert isinstance(cls.order_repo, OrderRepo)


def test_inject_interface_factory():
    factory_was_called = False

    class IBar:
        pass

    class Bar(IBar):
        pass

    @factory()
    def ibar_factory() -> IBar:
        nonlocal factory_was_called
        factory_was_called = True
        return Bar()

    @inject()
    def foo(bar: IBar):
        return isinstance(bar, IBar)

    with BeanContext():
        assert foo()

    assert factory_was_called


def test_inject_str_type(demo_beans):
    @inject()
    def foo(order_repo: 'OrderRepo'):
        return isinstance(order_repo, OrderRepo)

    with BeanContext():
        assert foo()


def test_directly_call_singleton():
    class Session:
        pass

    @singleton()
    class Foo:
        def __init__(self, session: Session):
            pass

    session = Session()
    foo = Foo(session)
    assert isinstance(foo, Foo)
