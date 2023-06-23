from .server.__main__ import SimpleRequestServer as Server
from .client.__main__ import SimpleCLIClient as Client

from . import settings
from .settings import *

__all__ = [
    "Server",
    "Client",
    *settings.__all__,
]
