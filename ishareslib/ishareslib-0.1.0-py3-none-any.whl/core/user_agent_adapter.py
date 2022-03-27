from abc import ABC, abstractmethod
from typing import Union


class UserAgentAdapter(ABC):
    def __init__(self, regeneration_limit: int = 3):
        self._user_agent: Union[str, None] = None
        self._regeneration_limit: int = regeneration_limit

    def get_user_agent(self) -> str:
        if self._user_agent is None:
            return self.new_user_agent()
        return self._user_agent

    def new_user_agent(self) -> str:
        user_agent: Union[str, None] = None
        for i in range(self._regeneration_limit):
            user_agent = self._gen_user_agent()
            if user_agent != self._user_agent:
                break

        if user_agent is None:
            raise ValueError("Could not choose a new user agent")

        if user_agent == self._user_agent:
            raise ValueError("User agent regeneration limit exceeded")

        self._user_agent = user_agent
        return self.get_user_agent()

    @abstractmethod
    def _gen_user_agent(self) -> Union[str, None]:  # pragma: no cover
        pass
