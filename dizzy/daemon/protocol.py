# this file implements a symmetric request/response protocol for the daemon
from dataclasses import dataclass, field
import json
import logging
import uuid
import zmq
import zmq.asyncio
from dataclass_wizard import JSONWizard

logger = logging.getLogger(__name__)


from typing import Any, Literal, Protocol, List

Status = Literal["created", "pending", "incomplete", "complete", "error"]


@dataclass
class Request(JSONWizard):
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    entity: str | None = None
    workflow: str | None = None
    service: str | None = None
    task: str | None = None
    args: dict = field(default_factory=dict)
    ctx: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.workflow is None and self.service is None:
            raise ValueError("Either workflow or service must be set")

        if self.workflow is not None and self.service is not None:
            raise ValueError("Only one of workflow or service can be set")

        if self.service is not None and self.task is None:
            raise ValueError("If service is set, task must be set")

        if self.entity is not None and self.workflow is None:
            raise ValueError("If entity is set, workflow must be set")

    def __str__(self):
        return f"Request(id={self.id}, workflow={self.workflow}, task={self.task}, args={self.args})"


@dataclass
class Response(JSONWizard):
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: Status = "incomplete"
    requester: str | None = None
    request: Request | None = None
    ctx: dict = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    info: dict[str, str] = field(default_factory=dict)
    result: Any | None = None

    def add_error(self, error: str, message: str):
        if error not in self.errors:
            self.errors[error] = [message]
        else:
            self.errors[error].append(message)

    def add_info(self, key: str, info: str):
        if key not in self.info:
            self.info[key] = [info]
        else:
            self.info[key].append(info)

    def set_result(self, result: Any):
        if self.status in ["complete", "error"]:
            raise RuntimeError(f"Cannot set result for {self.status=} packet.")

        self.result = result

    def set_status(self, status: Status):
        self.status = status

    def update_ctx(self, ctx: dict):
        self.ctx.update(ctx)

    @staticmethod
    def from_request(
        requester: str,
        request: Request,
        status: Literal[
            "created", "pending", "incomplete", "complete", "error"
        ] = "pending",
    ):
        response = Response()
        response.requester = requester
        response.request = request
        response.id = request.id
        response.ctx = request.ctx

        response.set_status(status)
        return response
