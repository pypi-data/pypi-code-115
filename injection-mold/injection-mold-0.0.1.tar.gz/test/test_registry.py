from mold import BeanRegistry
from mold import scan_beans


def test_simple_register():
    scan_beans('demo')
    beans = BeanRegistry.get().beans()
    expected_beans = {
        'OrderService',
        'InMemoryOrderRepo',
        'SqlOrderRepo',
        'demo_order_handler_foo',
        'demo_order_handler_bar',
    }

    bean_names = {b.name for b in beans}

    assert expected_beans == bean_names
