def accepts(*arg_types):
    def check_accepts(f):
        def function(*args, **kwargs):
            if len(arg_types) != len(args):
                raise ValueError('Types-Args length mismatch')
            for (arg, arg_type) in zip(args, arg_types):
                if not isinstance(arg, arg_type):
                    raise TypeError(f'{arg} must be of type {arg_type}')

            return f(*args, **kwargs)

        return function

    return check_accepts


def jit(*args, **kwargs):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        return wrapper
    return decorator
