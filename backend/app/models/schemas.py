

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.config import VALID_EVENT_TYPES, VALID_SEVERITIES, VALID_SERVICES, VALID_STATUSES




class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    lat: float
    lon: float
    location_label: Optional[str] = None
    status: str


class SourceCreate(BaseModel):
    name: str
    type: str  # camera | drone | simulation
    stream_url: str
    lat: float
    lon: float
    location_label: Optional[str] = None




class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: int
    event_type: str
    confidence: float
    severity: str
    service: str
    reason: Optional[str] = None
    operator_message: Optional[str] = None
    people_detected: Optional[int] = None
    smoke_detected: Optional[bool] = None
    lat: float
    lon: float
    status: str
    snapshot_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncidentStatusUpdate(BaseModel):
    status: str  # должен быть одним из VALID_STATUSES — проверяется в api/incidents.py


# Вход AI Dispatcher'а — то, что pipeline_runner.py передаёт после confirmation.
class DispatchRequest(BaseModel):
    event: str  # event_type
    confidence: float
    location: dict  # {"lat": ..., "lon": ...}
    people_detected: int = 0
    smoke_detected: bool = False


# Выход AI Dispatcher'а — строгий JSON-формат из ТЗ.
class DispatchResponse(BaseModel):
    severity: str
    service: str
    reason: str
    operator_message: str
