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

    class Config:
        populate_by_name = True
        extra = "allow"

class BaseResponse(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    status: Status = "incomplete"
    ctx: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        extra = "allow"


class BaseProtocol(BaseModel):
    Request: Type[BaseRequest]
    Response: Type[BaseResponse]

    class Config:
        arbitrary_types_allowed = True