from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time
from enum import Enum

class ReportType(Enum):
    single = 'single'
    periodic = 'periodic'

class ReportSubType(Enum):
    audit_report = 'general-audit-report'
    user_activity = 'user-audit-report'

class ReportFormat(Enum):
    pdf = 'pdf'
    csv = 'csv-plain'
    csv_semicolon = 'csv-semicolon-delimited'

class ReportFilter(BaseModel):
    fromDate: Optional[datetime]
    toDate: Optional[datetime]
    parentRoom: Optional[int]
    userId: Optional[int]
    operations: Optional[List[int]]

class ReportExecutionType(Enum):
    on_demand = 'on-demand'
    monthly = 'monthly'

class ReportExecution(BaseModel):
    type: ReportExecutionType
    timeOfDay: time
    dayOfMonth: int

class ReportTarget(BaseModel):
    id: int

class CreateReport(BaseModel):
    name: str
    type: ReportType
    subType: ReportSubType
    enabled: Optional[bool]
    execution: Optional[ReportExecution]
    formats: List[ReportFormat]
    filter: Optional[ReportFilter]
    target: ReportTarget


