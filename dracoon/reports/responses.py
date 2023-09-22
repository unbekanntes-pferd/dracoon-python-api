from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from dracoon.client.models import Range
from dracoon.reports.models import ReportFilter, ReportFormat, ReportSubType, ReportTarget, ReportType, ReportExecution

class ReportState(Enum):
    waiting = "waiting"
    processing = "processing"
    canceled = "canceled"
    finished = "finished"

class ReportError(BaseModel):
    message: Optional[str] = None
    code: Optional[int] = None
    detail: Optional[str] = None

class Report(BaseModel):
    id: Optional[int] = None
    created: Optional[datetime] = None
    lastModified: Optional[datetime] = None
    name: Optional[str] = None
    type: Optional[ReportType] = None
    subType: Optional[ReportSubType] = None
    enabled: Optional[bool] = None
    execution: Optional[ReportExecution] = None
    formats: Optional[ReportFormat] = None
    state: Optional[ReportState] = None
    error: Optional[ReportError] = None
    filter: Optional[ReportFilter] = None
    target: Optional[ReportTarget] = None

class ReportList(BaseModel):
    pagination: Range
    items: List[Report]

