from mold.type_dict import TypeDict


class Foo:
    pass


def test_set_string():
    td = TypeDict()
    td['Foo'] = 'bar'
    assert td[Foo] == 'bar'
    assert td['Foo'] == 'bar'
    assert td['event.Foo'] == 'bar'


def test_set_type():
    td = TypeDict()
    td[Foo] = 'bar'
    assert td[Foo] == 'bar'
    assert td['Foo'] == 'bar'


def test_contains_type():
    td = TypeDict()
    td[Foo] = 'bar'
    assert Foo in td
    assert 'Foo' in td
    assert 'event.Foo' in td


def test_default():
    td = TypeDict(default=list)
    assert type(td[Foo]) == list
