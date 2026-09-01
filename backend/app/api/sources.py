from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Source, SourceStatus
from app.models.schemas import SourceOut, SourceCreate
from app.services.worker_manager import manager as worker_manager

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()


@router.post("", response_model=SourceOut)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = Source(
        name=payload.name,
        type=payload.type,
        stream_url=payload.stream_url,
        lat=payload.lat,
        lon=payload.lon,
        location_label=payload.location_label,
        status=SourceStatus.inactive,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/{source_id}/start")
def start_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source не найден")

    ok, message = worker_manager.start_worker(source.id, source.stream_url, source.lat, source.lon)
    if not ok:
        raise HTTPException(409, message)

    source.status = SourceStatus.active
    db.commit()
    return {"status": "started", "source_id": source_id}


@router.post("/{source_id}/stop")
def stop_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source не найден")

    ok, message = worker_manager.stop_worker(source_id)
    if not ok:
        raise HTTPException(409, message)

    source.status = SourceStatus.inactive
    db.commit()
    return {"status": "stopped", "source_id": source_id}
