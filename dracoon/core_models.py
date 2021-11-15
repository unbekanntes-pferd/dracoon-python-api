""" 
Core models required by other models 

"""


from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime
from enum import Enum
import json

class Range(BaseModel):
    offset: int
    limit: int
    total: int

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: datetime

class ErrorMessage(BaseModel):
    code: int
    message: str
    debugInfo: Optional[str]
    errorCode: Optional[int]



""" 
LEGACY API 0.4.x – DO NOT MODIFY

"""

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

class ApiDestination(Enum):
    Core = 'core'
    Reporting = 'reporting'
    Branding = 'branding'

class IDList(BaseModel):
    ids: List[int]

def model_to_JSON(model: BaseModel):

    if not isinstance(model, list):
        return json.loads(model.json(exclude_unset=True))
    else:
        json_str = "["
        for item in model:
            json_str += item.json(exclude_unset=True)

        json_str += "]"
  
        return json.loads(json_str)



    
