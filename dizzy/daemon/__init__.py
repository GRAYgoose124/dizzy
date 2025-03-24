from .server.__main__ import SimpleRequestServer, DaemonEntityManager
from .client.cli import SimpleCLIClient
from .client.asy import SimpleAsyncClient

from .abstract_protocol import BaseRequest, BaseResponse, BaseProtocol

from .settings import SettingsManager

try:
    SM = SettingsManager()
    all_entities = SM.settings.all_entities
except Exception as e:
    print(f"Error initializing SettingsManager: {e}")
    SM = None


__all__ = [
    "SimpleRequestServer",
    "SimpleCLIClient",
    "SimpleAsyncClient",

    "DaemonEntityManager",

    "BaseRequest",
    "BaseResponse",
    "BaseProtocol",
]
