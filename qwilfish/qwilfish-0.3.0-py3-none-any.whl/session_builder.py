'''Builds a session based on the config it gets'''


GRAMMAR = "grammar"
COURIER = "courier"

grammar_build_funcs = {}
courier_build_funcs = {}

build_funcs_lookup = {GRAMMAR: grammar_build_funcs,
                      COURIER: courier_build_funcs}

def register_grammar(identifier, build_func):
    _register(GRAMMAR, identifier, build_func)

def register_courier(identifier, build_func):
    _register(COURIER, identifier, build_func)

def build_grammar(**kwargs):
    return _build(GRAMMAR, **kwargs)

def build_courier(**kwargs):
    return _build(COURIER, **kwargs)

def _register(type, identifier, build_func):
    build_funcs = build_funcs_lookup[type]
    build_funcs[identifier] = build_func

def _build(type, **kwargs):
    build_funcs = build_funcs_lookup[type]

    kwargs_copy = kwargs.copy()
    identifier = kwargs_copy.pop("identifier", None)

    if not identifier:
        raise ValueError("No identifier found while configuring plugin!")

    try:
        build_func = build_funcs[identifier]
        return build_func(**kwargs_copy)
    except KeyError:
        raise ValueError(f"Plugin '{identifier}' has not been registered!")
