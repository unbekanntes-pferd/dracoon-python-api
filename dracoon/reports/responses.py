from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from pydantic.env_settings import BaseSettings
from dracoon.client.models import Range
from dracoon.reports.models import ReportFilter, ReportFormat, ReportSubType, ReportTarget, ReportType, ReportExecution

class ReportState(Enum):
    waiting = "waiting"
    processing = "processing"
    canceled = "canceled"
    finished = "finished"

class ReportError(BaseSettings):
    message: Optional[str]
    code: Optional[int]
    detail: Optional[str]

class Report(BaseModel):
    id: Optional[int]
    created: Optional[datetime]
    lastModified: Optional[datetime]
    name: Optional[str]
    type: Optional[ReportType]
    subType: Optional[ReportSubType]
    enabled: Optional[bool]
    execution: Optional[ReportExecution]
    formats: Optional[ReportFormat]
    state: Optional[ReportState]
    error: Optional[ReportError]
    filter: Optional[ReportFilter]
    target: Optional[ReportTarget]

class ReportList(BaseModel):
    pagination: Range
    items: List[Report]

