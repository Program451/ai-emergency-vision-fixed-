from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import VALID_STATUSES
from app.database import get_db
from app.models.incident import Incident
from app.models.schemas import IncidentOut, IncidentStatusUpdate
from app.notifications.telegram import send_incident_notification
from app.api.ws_manager import manager as ws_manager

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    return query.order_by(Incident.created_at.desc()).all()


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident не найден")
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentOut)
async def update_status(incident_id: str, payload: IncidentStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(400, f"Недопустимый статус. Разрешены: {VALID_STATUSES}")

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident не найден")

    incident.status = payload.status
    db.commit()
    db.refresh(incident)

    incident_dict = {
        "id": incident.id,
        "status": incident.status.value,
    }
    await ws_manager._broadcast_async({"type": "incident_updated", "incident": incident_dict})

    # Ручная передача оператору ("Передать оператору" -> status=SENT) —
    # тоже триггерит Telegram-уведомление, если ещё не отправлялось автоматически.
    if payload.status == "SENT":
        full_incident = {
            "id": incident.id,
            "event_type": incident.event_type.value,
            "severity": incident.severity.value,
            "service": incident.service.value,
            "lat": incident.lat,
            "lon": incident.lon,
            "confidence": incident.confidence,
            "operator_message": incident.operator_message,
        }
        send_incident_notification(full_incident)

    return incident
