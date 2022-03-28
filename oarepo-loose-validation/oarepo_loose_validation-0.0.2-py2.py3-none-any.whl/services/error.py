class OarepoError(str):
    def __init__(self, content, struct= True):
        self.s = content
        self.struct = struct
        self.params = {}

    def __new__(cls, content, *args, **kwargs ):
        return str.__new__(cls, content)

    def format(self, *args, **kwargs):  # known special case of str.format
        self.params = kwargs
        return self
