from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, time
from enum import Enum


class ReportType(Enum):
    single = "single"
    periodic = "periodic"


class ReportSubType(Enum):
    audit_report = "general-audit-report"
    user_activity = "user-audit-report"


class ReportFormat(Enum):
    pdf = "pdf"
    csv = "csv-plain"
    csv_semicolon = "csv-semicolon-delimited"


class ReportFilter(BaseModel):
    fromDate: Optional[str] = None
    toDate: Optional[str] = None
    parentRoom: Optional[int] = None
    userId: Optional[int] = None
    operations: Optional[List[int]] = None


class ReportExecutionType(Enum):
    on_demand = "on-demand"
    monthly = "monthly"


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
    enabled: Optional[bool] = None
    execution: Optional[ReportExecution] = None
    formats: List[ReportFormat] = None
    filter: Optional[ReportFilter] = None
    target: ReportTarget
    model_config = ConfigDict(use_enum_values=True)
