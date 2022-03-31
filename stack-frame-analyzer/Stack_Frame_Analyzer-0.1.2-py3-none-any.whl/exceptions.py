class InvalidFrameDepth(ValueError):
    """Exception raised for errors in get_frame_context method of StackFrameAnalyzer class.

    Args:
        message: explanation of the error
    """

    def __init__(self) -> "InvalidFrameDepth":
        self.message = (
            "Invalid stack_frame_depth input value. It must be a natural number."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class FrameDepthOutOfRange(ValueError):
    """Exception raised for errors in get_frame_context method of StackFrameAnalyzer class.

    Args:
        message: explanation of the error
    """

    def __init__(self) -> "InvalidFrameDepth":
        self.message = (
            "Caller's stack is not deep enough. stack_frame_depth is out of range."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class StackFrameAnalyzerException(Exception):
    """Exception raised for errors in get_frame_context method of StackFrameAnalyzer class.

    Args:
        message: explanation of the error
    """

    def __init__(self) -> "InvalidFrameDepth":
        self.message = (
            "Internal error from get_frame_context method of StackFrameAnalyzer class."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"
