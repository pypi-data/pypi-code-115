from typing import Optional

from nautilus_trader.live.config import TradingNodeConfig as NautilusTradingNodeConfig

from nacre.actors.config import ExposerConfig
from nacre.actors.config import PubSubConfig


class TradingNodeConfig(NautilusTradingNodeConfig):
    """
    Configuration for ``TradingNode`` instances.

    pubsub: PubSubConfig, optional
        The config for external msgbus pubsub
    exposer: ExposerConfig, optional
        The config for exposer
    """

    pubsub: Optional[PubSubConfig] = None
    exposer: Optional[ExposerConfig] = None
