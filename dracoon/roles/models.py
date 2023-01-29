from typing import List
from pydantic import BaseModel

class GroupIds(BaseModel):
    ids: List[int]
    
class UserIds(BaseModel):
    ids: List[int]
    