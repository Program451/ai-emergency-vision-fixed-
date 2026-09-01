

import threading
import time

import cv2

from app.config import SNAPSHOT_INTERVAL_SECONDS, SNAPSHOTS_DIR
from app.database import SessionLocal
from app.models.incident import Incident, Source, SourceStatus
from app.vision.video_reader import VideoReader
from app.vision.detector import get_detector
from app.vision.confirmation import ConfirmationEngine
from app.vision.annotate import draw_detections
from app.dispatcher.ai_dispatcher import dispatch
from app.notifications.telegram import send_incident_notification
from app.api.ws_manager import manager as ws_manager

# Один ConfirmationEngine на процесс — буферы разделены по source_id внутри него,
# так что несколько worker'ов могут безопасно использовать общий инстанс.
_confirmation_engine = ConfirmationEngine()


def run_pipeline_sync(source_id: int, stream_url: str, lat: float, lon: float, stop_event: threading.Event, target_event: str = None):
    """
    Блокирующая функция — рассчитана на запуск в отдельном потоке
    (см. worker_manager.WorkerManager.start_worker).

    target_event задаётся только для Simulation Mode — тогда MockDetector
    "видит" именно нужное событие, обеспечивая предсказуемое демо.
    """
    detector = get_detector(target_event=target_event)

    try:
        reader = VideoReader(stream_url)
        reader.open()
    except Exception as e:
        print(f"[pipeline_runner] source={source_id}: не удалось открыть видео: {e}")
        _mark_source_status(source_id, SourceStatus.inactive)
        return

    print(f"[pipeline_runner] source={source_id} started (target_event={target_event})")
    last_snapshot_time = 0.0

    try:
        while not stop_event.is_set():
            frame_found = False
            for frame_index, inference_frame, original_frame in reader.frames():
                if stop_event.is_set():
                    break
                frame_found = True

                raw_detections = detector.detect(inference_frame)
                confirmed_events = _confirmation_engine.push_frame(source_id, raw_detections)

                for event in confirmed_events:
                    _handle_confirmed_event(source_id, lat, lon, event)

                now = time.time()
                if now - last_snapshot_time >= SNAPSHOT_INTERVAL_SECONDS:
                    annotated_frame = draw_detections(original_frame, raw_detections)
                    cv2.imwrite(str(SNAPSHOTS_DIR / f"{source_id}.jpg"), annotated_frame)
                    last_snapshot_time = now

                    # Лёгкий live-апдейт для Dashboard (не incident, просто "что видит ИИ прямо сейчас"),
                    # чтобы фронт мог подсветить статус трекинга ещё до подтверждения события.
                    if raw_detections:
                        ws_manager.broadcast_threadsafe({
                            "type": "live_detection",
                            "source_id": source_id,
                            "detections": [
                                {"class": d["class"], "confidence": d["confidence"]} for d in raw_detections
                            ],
                        })

            # Файл кончился (или simulation-видео доиграло) — для Simulation Mode
            # это нормальный конец сценария, останавливаем worker.
            if not frame_found or target_event is not None:
                break

            time.sleep(0.05)
    finally:
        reader.close()
        _confirmation_engine.reset(source_id)
        _mark_source_status(source_id, SourceStatus.inactive)
        print(f"[pipeline_runner] source={source_id} stopped")


def _handle_confirmed_event(source_id: int, lat: float, lon: float, event: dict):
    """Подтверждённое событие -> AI Dispatcher -> Incident в БД -> broadcast -> Telegram."""
    dispatch_result = dispatch(
        event=event["event_type"],
        confidence=event["confidence"],
        location={"lat": lat, "lon": lon},
        people_detected=event["people_detected"],
        smoke_detected=event["smoke_detected"],
    )

    db = SessionLocal()
    try:
        incident = Incident(
            source_id=source_id,
            event_type=event["event_type"],
            confidence=event["confidence"],
            severity=dispatch_result["severity"],
            service=dispatch_result["service"],
            reason=dispatch_result["reason"],
            operator_message=dispatch_result["operator_message"],
            people_detected=event["people_detected"],
            smoke_detected=event["smoke_detected"],
            lat=lat,
            lon=lon,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        incident_dict = {
            "id": incident.id,
            "source_id": incident.source_id,
            "event_type": incident.event_type.value,
            "confidence": incident.confidence,
            "severity": incident.severity.value,
            "service": incident.service.value,
            "reason": incident.reason,
            "operator_message": incident.operator_message,
            "people_detected": incident.people_detected,
            "smoke_detected": incident.smoke_detected,
            "lat": incident.lat,
            "lon": incident.lon,
            "status": incident.status.value,
            "created_at": incident.created_at.isoformat(),
        }

        ws_manager.broadcast_threadsafe({"type": "incident_created", "incident": incident_dict})

        # CRITICAL-события отправляются оператору в Telegram автоматически;
        # остальные — по кнопке "Передать оператору" (см. api/incidents.py, PATCH status=SENT).
        if incident.severity.value == "CRITICAL":
            send_incident_notification(incident_dict)

        print(f"[pipeline_runner] incident created: {incident.id} ({incident.event_type.value}, {incident.severity.value})")
    finally:
        db.close()


def _mark_source_status(source_id: int, status: SourceStatus):
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if source:
            source.status = status
            db.commit()
    finally:
        db.close()
