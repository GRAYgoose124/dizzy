from dataclasses import dataclass
from pydantic import BaseModel, Field, validator
from typing import Any, Dict, Generic, List, Literal, Optional, Type
import uuid
from dataclass_wizard import JSONWizard

Status = Literal["created", "pending", "incomplete", "complete", "error"]

# TODO: Make id bytes
class BaseRequest(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ctx: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        extra = "allow"

    def set_option(self, key: str, value: Any):
        self.options[key] = value
    
    
class BaseResponse[Rq: BaseRequest](BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    request: Optional[Rq] = None
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
        self = cls()
        self.request = request
        self.status = status
        return self

class BaseProtocol[Rq: BaseRequest, Rs: BaseResponse[BaseRequest]](BaseModel):
    Request: Type[Rq]
    Response: Type[Rs]

    class Config:
        arbitrary_types_allowed = True