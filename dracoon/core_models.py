from pydantic import BaseModel
from typing import Any, Optional, List
from enum import Enum
import json

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







    
