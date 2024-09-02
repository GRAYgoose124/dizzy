from .server.__main__ import SimpleRequestServer as Server
from .server.__main__ import DaemonEntityManager

from .client.cli import SimpleCLIClient as CLICient
from .client.asy import SimpleAsyncClient

from .abstract_protocol import BaseRequest, BaseResponse

from .settings import SettingsManager

try:
    SM = SettingsManager()
    all_entities = SM.settings.all_entities
except Exception as e:
    print(f"Error initializing SettingsManager: {e}")
    SM = None


__all__ = [
    "Server",
    "CLICient",
    "SimpleAsyncClient",
    "DaemonEntityManager",
    "BaseRequest",
    "BaseResponse",
]
