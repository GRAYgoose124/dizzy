from typing import Optional, Dict, Any, Type
from pydantic import Field

from dizzy.daemon.abstract_protocol import BaseRequest, BaseResponse, BaseProtocol


class DefaultRequest(BaseRequest):
    entity: Optional[str] = None
    workflow: Optional[str] = None
    task: Optional[str] = None
    service: Optional[str] = None

    def __str__(self):
        return f"Request(id={self.id}, workflow={self.workflow}, task={self.task}, step_options={self.step_options})"

class DefaultResponse(BaseResponse[DefaultRequest]):
    ctx: Dict[str, Any] = Field(default_factory=dict)

    def update_ctx(self, ctx: dict):
        self.ctx.update(ctx)

class DefaultProtocol(BaseProtocol[DefaultRequest, DefaultResponse]):
    Request: Type[DefaultRequest] = DefaultRequest
    Response: Type[DefaultResponse] = DefaultResponse


DizzyProtocol = DefaultProtocol