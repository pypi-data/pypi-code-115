from sym.sdk.exceptions.sym_exception import SymException


class IdentityError(SymException):
    """This is the base class for errors that occur when managing identities.

    Args:
        name: The name of the exception (used as the second part of the error code, e.g. COULD_NOT_SAVE)
        message: The exception message to display
    """

    def __init__(self, name: str, message: str, error_type: str = "Identity"):
        super().__init__(error_type=error_type, name=name, message=message)


class CouldNotSaveError(IdentityError):
    """This error is raised in cases where a :class:`~sym.sdk.user.UserIdentity`
    was unable to be saved.
    """

    def __init__(self, message: str):
        super().__init__("COULD_NOT_SAVE", message)
