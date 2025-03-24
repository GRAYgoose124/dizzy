from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Generic, List, Literal, Optional, Type
from pathlib import Path
import uuid
from dataclass_wizard import JSONWizard

Status = Literal[
    "created",
    "pending",
    "incomplete",
    "complete",
    "error",
    "finished_with_errors",
    "cancelled",
    "stopped",
]


# TODO: Make id bytes
class BaseRequest(BaseModel):
    id: Optional[str] = None
    ctx: Dict[str, Any] = Field(default_factory=dict)
    step_options: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        extra = "allow"

    def set_option(self, key: str, value: Any):
        self.step_options[key] = value


class BaseResponse[Rq: BaseRequest](BaseModel):
    id: Optional[str] = None
    request: Rq
    requester: Optional[str] = None

    status: Status = "incomplete"
    errors: Dict[str, List[str]] = Field(default_factory=dict)
    info: Dict[str, List[str]] = Field(default_factory=dict)
    result: Any = None

    class Config:
        populate_by_name = True
        extra = "allow"

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

    @classmethod
    def from_request(cls, request: Rq, status: Status = "pending"):
        self = cls(request=request, status=status)
        return self


class BaseProtocol[Rq: BaseRequest, Rs: BaseResponse[Rq]](BaseModel):
    Request: Type[Rq]
    Response: Type[Rs]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, protocol_dir: Path):
        import importlib

        # use importlib to load the protocol from protocol_dir/protocol.py using spec
        spec = importlib.util.spec_from_file_location(
            "protocol", Path(protocol_dir) / "protocol.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(
            module, "DizzyProtocol"
        ), f"Protocol module must have a DizzyProtocol class"

        return module.DizzyProtocol()


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
