# this file implements a symmetric request/response protocol for the daemon
from dataclasses import dataclass, field
import logging
import uuid
import zmq
import zmq.asyncio
from dataclass_wizard import JSONWizard

logger = logging.getLogger(__name__)


from typing import Any, Literal, Protocol, List


@dataclass
class DataPacket(JSONWizard):
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: Literal[
        "created", "pending", "incomplete", "complete", "error"
    ] = "incomplete"
    errors: list[str]
    info: list[str]
    result: Any
    request: str
    ctx: dict
