""" 
Client models (basic response models and client config)

"""

from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict, Optional, Union
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

class OAuth2ConnectionType(Enum):
    """ enum as connection type for DRACOONClient """
    """ supports authorization code flow, password flow and refresh token """
    password_flow = 1
    auth_code = 2
    refresh_token = 3

@dataclass
class DRACOONConnection:
    """ DRACOON connection with tokens and validity """
    connected_at: datetime
    access_token: str
    access_token_validity: int
    refresh_token: str
    
class RetryConfig(BaseModel):
    retry: Any
    stop: Any
    wait: Any
    reraise: bool