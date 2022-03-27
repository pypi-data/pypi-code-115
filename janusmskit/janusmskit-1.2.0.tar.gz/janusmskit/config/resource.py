from typing import Text

from janusmskit.config import get_conf


class ConfigResource:

    config_resource: Text = ""

    def __init__(self, *args, **kwargs):
        self.config = get_conf(service=self.config_resource, empty_init=True, uppercase=False, *args, **kwargs)
