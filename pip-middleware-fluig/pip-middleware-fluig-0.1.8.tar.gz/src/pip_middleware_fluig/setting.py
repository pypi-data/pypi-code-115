from typing import Optional
from pydantic import BaseSettings, Field
from typing import Optional

_settings = None


class Settings(BaseSettings):
    environment: Optional[str] = Field(env="ENVIRONMENT")

    @classmethod
    def get_setting(cls):

        global _settings
        if _settings is None:
            _settings = Settings()

        return _settings
