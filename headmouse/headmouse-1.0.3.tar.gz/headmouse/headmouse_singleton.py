class HeadMouseSingleton(type):
    """
    Metaclass, declared to prevent the creation of two or more objects of the 
    HeadMouse class, since the camera resource can't be shared.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                HeadMouseSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
