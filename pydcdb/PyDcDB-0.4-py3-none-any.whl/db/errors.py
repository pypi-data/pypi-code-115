class DscPyDBException(Exception):
    pass

class RecordNotFound(DscPyDBException):
    def __init__(self) -> None:
        super().__init__("No Record was found")