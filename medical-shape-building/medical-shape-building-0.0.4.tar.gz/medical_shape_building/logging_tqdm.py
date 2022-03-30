import io
import logging


class TqdmToLogger(io.StringIO):
    """Output stream for TQDM which will output to logger module instead of the StdOut.

    From: https://stackoverflow.com/a/38895482
    """

    logger = None
    level = None
    buf = ""

    def __init__(self, logger, level: int = logging.DEBUG):
        super().__init__()
        self.logger = logger
        self.level = level

    def write(self, buf):
        self.buf = buf.strip("\r\n\t ")

    def flush(self):
        if not self.buf:
            return
        self.logger.log(self.level, self.buf)
