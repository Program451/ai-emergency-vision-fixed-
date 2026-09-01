

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SourceType(str, enum.Enum):
    camera = "camera"
    drone = "drone"
    simulation = "simulation"


class SourceStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class EventType(str, enum.Enum):
    car_accident = "car_accident"
    fire = "fire"
    smoke = "smoke"
    person_fallen = "person_fallen"
    pothole = "pothole"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Service(str, enum.Enum):
    EMERGENCY_MEDICAL = "EMERGENCY_MEDICAL"
    FIRE_DEPARTMENT = "FIRE_DEPARTMENT"
    POLICE = "POLICE"
    ROAD_MAINTENANCE = "ROAD_MAINTENANCE"


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    SENT = "SENT"
    RESOLVED = "RESOLVED"


def _uuid() -> str:
    return uuid.uuid4().hex[:8]


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(Enum(SourceType), nullable=False)
    stream_url = Column(String, nullable=False)  # RTSP-адрес или путь к видеофайлу
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    location_label = Column(String, nullable=True)  # человекочитаемое описание, напр. "Main St / 5th Ave"
    status = Column(Enum(SourceStatus), nullable=False, default=SourceStatus.inactive)
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("Incident", back_populates="source")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=_uuid)  # напр. "a1b2c3d4"
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)

    event_type = Column(Enum(EventType), nullable=False)
    confidence = Column(Float, nullable=False)  # агрегированная confidence по confirmation-окну

    severity = Column(Enum(Severity), nullable=False)
    service = Column(Enum(Service), nullable=False)
    reason = Column(Text, nullable=True)
    operator_message = Column(Text, nullable=True)

    people_detected = Column(Integer, nullable=True)
    smoke_detected = Column(Boolean, nullable=True)

    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.NEW)
    snapshot_path = Column(String, nullable=True)  # кадр момента детекции — оператор видит, что увидел AI

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("Source", back_populates="incidents")
