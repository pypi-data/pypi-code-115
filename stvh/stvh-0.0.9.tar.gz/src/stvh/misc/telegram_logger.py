from datetime import datetime
from typing import Any, Callable, Optional

import requests


class TelegramLogger:
    """

    - Visit `https://api.telegram.org/bot<token>/getUpdates` to get `chat_id`.

    Example:
        >>> import os
        >>> os.environ["TELEGRAM_BOT_TOKEN"] = "####"
        >>> os.environ["TELEGRAM_BOT_CHAT_ID"] = "####"
        >>> bot = stvh.misc.TelegramLogger(callback=print)
        >>> bot.send("Hello, world!")
        Hello, world!
    """

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        callback: Optional[Callable[[str], Any]] = None,
    ) -> None:
        """TODO

        Args:
            token (str):
            chat_id (str):
        """
        import os

        token = os.getenv("TELEGRAM_BOT_TOKEN", default="") if token is None else token
        chat_id = os.getenv("TELEGRAM_BOT_CHAT_ID", default="") if chat_id is None else chat_id

        self._url: str = f"https://api.telegram.org/bot{token}/sendMessage"
        self._chat_id: str = chat_id
        self._callback: Optional[Callable[[str], Any]] = callback
        self._msgs: list[str] = []

    def add(self, msg: str = "") -> None:
        """TODO

        Args:
            msg (str):
        """
        self._msgs.append(TelegramLogger.format_msg(msg))

        if self._callback is not None:
            self._callback(msg)

    def flush(self) -> None:
        """TODO"""
        if len(self._msgs) == 0:
            return

        resp = requests.post(
            url=self._url,
            params={
                "chat_id": self._chat_id,
                "text": "\n".join(self._msgs),
            },
        )
        resp.raise_for_status()  # what is the purpose of this line?
        del self._msgs[:]

    def send(self, msg: str = "") -> None:
        """TODO

        Args:
            msg (str):
        """
        self.add(msg)
        self.flush()

    @staticmethod
    def format_msg(msg: str = "") -> str:
        """TODO

        Args:
            msg (str):

        Returns:
        """
        return f"[{datetime.now().strftime('%b %d %H:%M:%S')}]\n{msg}"
