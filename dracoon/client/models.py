""" 
Core models required by other models 

"""


from pydantic import BaseModel
from typing import Any, Optional, List
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

