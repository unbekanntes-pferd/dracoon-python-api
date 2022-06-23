""" 
Core models required by other models 

"""


from pydantic import BaseModel
from typing import Dict, Optional, Union
from datetime import datetime


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

# adheres to proxy model from httpx (dict with http / https and respective str) or single str
ProxyConfig = Union[Dict[str, str], str]