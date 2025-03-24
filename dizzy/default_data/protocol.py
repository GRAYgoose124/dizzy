from pydantic import Field, validator
from typing import Any, Dict, Optional, List, Type

from dizzy.daemon.abstract_protocol import (
    BaseRequest,
    BaseResponse,
    Status,
    BaseProtocol,
)


class Request(BaseRequest):
    entity: Optional[str] = None
    workflow: Optional[str] = None
    task: Optional[str] = None
    args: Dict[str, Any] = Field(default_factory=dict)

    def __str__(self):
        return f"Request(id={self.id}, workflow={self.workflow}, task={self.task}, options={self.options})"


class Response(BaseResponse[Request]):
    ctx: Dict[str, Any] = Field(default_factory=dict)

    def update_ctx(self, ctx: dict):
        self.ctx.update(ctx)

    @classmethod
    def from_request(
        cls,
        requester: str,
        request: Request,
        status: Status = "pending",
    ):
        return cls(
            requester=str(requester),
            request=request,
            id=request.id,
            ctx=request.ctx,
            status=status,
        )


class DizzyProtocol(BaseProtocol[Request, Response]):
    Request: Type[Request] = Request
    Response: Type[Response] = Response
