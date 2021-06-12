from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum

class CallMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

class ApiCall(BaseModel):
    url: str
    body: Optional[Any]
    files: Optional[Any]
    method: CallMethod
    content_type: Optional[str]



    
