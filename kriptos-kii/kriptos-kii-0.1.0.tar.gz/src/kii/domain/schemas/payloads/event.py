from .ipayload import IPayload


class Event(IPayload):

    def __init__(self):
        ...

    def to_dict(self):
        ...
