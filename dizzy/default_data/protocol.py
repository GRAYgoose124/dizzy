from pydantic import Field, validator
from typing import Any, Dict, Optional, List

from dizzy.daemon.abstract_protocol import BaseRequest, BaseResponse, Status, BaseProtocol

class Request(BaseRequest):
    entity: Optional[str] = None
    workflow: Optional[str] = None
    task: Optional[str] = None
    args: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)

    def __str__(self):
        return f"Request(id={self.id}, workflow={self.workflow}, task={self.task}, options={self.options})"

class Response(BaseResponse):
    requester: Optional[str] = None
    request: Optional[Request] = None
    errors: Dict[str, List[str]] = Field(default_factory=dict)
    info: Dict[str, List[str]] = Field(default_factory=dict)
    result: Any = None

    # TODO: abstract methods
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
            status=status
        )
    

Protocol = BaseProtocol(Request=Request, Response=Response)