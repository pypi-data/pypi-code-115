
class InvalidPayloadException(BaseException):
    message = "Invalid payload. Does not match the type of insight chosen"


class MalformedPayloadException(BaseException):
    message = "The insight payload has not been correctly parameterized"
