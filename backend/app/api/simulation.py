from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import SIMULATION_SCENARIOS
from app.database import get_db
from app.models.incident import Source, SourceType, SourceStatus
from app.services.worker_manager import manager as worker_manager
from app.vision.synthetic_video import ensure_placeholder_video

router = APIRouter(prefix="/simulate", tags=["simulation"])


def _get_or_create_simulation_source(db: Session, scenario_key: str) -> Source:
    """
    Каждый сценарий имеет свой постоянный simulation-source в Source Registry
    (создаётся один раз, дальше переиспользуется) — так журнал/дашборд
    видят стабильный "источник" вроде "SIM-car_accident", а не плодят новые
    записи при каждом запуске.
    """
    scenario = SIMULATION_SCENARIOS[scenario_key]
    name = f"SIM-{scenario_key}"

    source = db.query(Source).filter(Source.name == name).first()
    if source:
        return source

    source = Source(
        name=name,
        type=SourceType.simulation,
        stream_url=scenario["video_file"],
        lat=scenario["lat"],
        lon=scenario["lon"],
        location_label=f"Simulation: {scenario['label']}",
        status=SourceStatus.inactive,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/{scenario_key}")
def run_simulation(scenario_key: str, db: Session = Depends(get_db)):
    if scenario_key not in SIMULATION_SCENARIOS:
        raise HTTPException(404, f"Неизвестный сценарий. Доступны: {list(SIMULATION_SCENARIOS.keys())}")

    scenario = SIMULATION_SCENARIOS[scenario_key]
    ensure_placeholder_video(scenario["video_file"], scenario["label"])

    source = _get_or_create_simulation_source(db, scenario_key)

    ok, message = worker_manager.start_worker(
        source.id,
        source.stream_url,
        source.lat,
        source.lon,
        target_event=scenario["event_type"],
    )
    if not ok:
        raise HTTPException(409, message)

    source.status = SourceStatus.active
    db.commit()

    return {"status": "started", "scenario": scenario_key, "source_id": source.id}
