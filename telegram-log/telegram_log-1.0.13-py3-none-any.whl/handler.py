import cgitb
import contextlib
import copy
import datetime
import io
import logging
import logging.config
import types
import typing

import telegram


ExcInfoType = typing.Tuple[typing.Type[BaseException], BaseException, types.TracebackType]


class TelegramHandler(logging.Handler):
    bot: telegram.Bot
    chat_id: int
    exc_logger: logging.Logger

    def __init__(
            self,
            /,
            token: str,
            chat_id: int,
            *,
            level: int = logging.NOTSET,
    ):
        logging.Handler.__init__(self, level=level)
        self.bot = telegram.Bot(token)
        self.chat_id = chat_id
        self.exc_logger = self.create_logger()

    @staticmethod
    def create_logger() -> logging.Logger:
        name = __name__
        logger = logging.getLogger(name)
        logger.propagate = False
        return logger

    @staticmethod
    def get_tb_data(exc_info: ExcInfoType) -> io.BytesIO:
        encoding: str = 'utf-8'
        context_width = 11
        string_io_buffer = io.StringIO()
        cgitb.Hook(
            context=context_width,
            file=string_io_buffer,
        ).handle(
            info=exc_info
        )
        string_io_buffer.seek(0)
        bytes_io_buffer = io.BytesIO(string_io_buffer.read().encode(encoding))
        bytes_io_buffer.seek(0)
        return bytes_io_buffer

    @staticmethod
    def prepare(log_data: str, length: int):
        message = log_data[:length]
        return message

    def emit(self, record: logging.LogRecord):
        try:
            if record.exc_info is None:
                self.send_plain_text(record)
            else:
                self.send_traceback(record)
        except Exception as exc:
            self.exc_logger.exception(exc)

    def send_traceback(self, record: logging.LogRecord):
        file_pattern = 'python_tb_%Y-%m-%d_%H_%M_%S.html'
        tb_data = self.get_tb_data(record.exc_info)  # type: ignore
        with contextlib.closing(tb_data):
            caption = self.get_exc_caption_text(record)
            self.bot.send_document(
                self.chat_id,
                tb_data,
                filename=datetime.datetime.now().strftime(file_pattern),
                caption=caption,
            )

    def get_exc_caption_text(self, record: logging.LogRecord) -> str:
        caption_length = 200
        no_exc_record = self.get_no_exc_record_copy(record)
        caption = self.prepare(self.format(no_exc_record), caption_length)
        return typing.cast(str, caption)

    @staticmethod
    def get_no_exc_record_copy(record: logging.LogRecord) -> logging.LogRecord:
        no_exc_record = copy.copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None
        return no_exc_record

    def send_plain_text(self, record: logging.LogRecord):
        message_length = 4096
        message = self.prepare(self.format(record), message_length)
        self.bot.send_message(self.chat_id, message)
