class UnauthorizedError(Exception):
    """Raised when HTTP 401 received from API"""


class EmptyResponseError(Exception):
    """Raised when empty response received"""


class NoSuchItemError(Exception):
    """Raised when no item found with specified id"""


class NotFoundError(Exception):
    """Raised when tried to get non-existing endpoint"""
