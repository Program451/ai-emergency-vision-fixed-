

import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config import (
    ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE_MB, UPLOADS_DIR,
    ALLOWED_PHOTO_EXTENSIONS, MAX_PHOTO_SIZE_MB, PHOTOS_DIR, INFERENCE_RESOLUTION,
)
from app.database import get_db
from app.models.incident import Source, SourceType, SourceStatus
from app.models.schemas import SourceOut
from app.services.worker_manager import manager as worker_manager
from app.vision.detector import get_detector
from app.vision.annotate import draw_detections, LABELS_RU

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _safe_name(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", stem)[:40] or "video"
    return stem


def _transcode_to_playable_mp4(src_path: Path) -> Path:
    """
    БАГФИКС "некоторые видео не загружаются правильно": .mov/.avi/.mkv и
    даже часть .mp4 с телефонов/дронов используют кодеки, которые не
    понимает урезанная сборка ffmpeg внутри opencv-python-headless —
    cv2.VideoCapture().isOpened() возвращал False, pipeline не стартовал,
    Source навсегда оставался "inactive" без единого кадра/снапшота.

    Решение: сразу после загрузки прогоняем файл через системный ffmpeg
    в гарантированно читаемый H.264/AAC mp4 (+faststart). Если ffmpeg не
    смог (битый файл, нет ffmpeg в системе) — используем оригинал как есть,
    ничего не роняем.
    """
    if shutil.which("ffmpeg") is None:
        return src_path  # ffmpeg не установлен (например, локальный запуск без Docker) — работаем как раньше

    out_path = src_path.with_name(src_path.stem + "_playable.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src_path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        if result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
            src_path.unlink(missing_ok=True)  # оригинал больше не нужен, храним только конвертированный
            return out_path
    except Exception as e:
        print(f"[uploads] ffmpeg transcode failed for {src_path.name}: {e}")

    out_path.unlink(missing_ok=True)
    return src_path  # конвертация не удалась — пробуем открыть оригинал напрямую


@router.post("/video", response_model=SourceOut)
async def upload_demo_video(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    lat: float = Form(42.9000),
    lon: float = Form(71.3667),
    location_label: str | None = Form(None),
    autostart: bool = Form(True),
    db: Session = Depends(get_db),
):
    """
    Принимает видеофайл, сохраняет во временную папку, создаёт под него
    Source (type=camera) и — если autostart=True — сразу запускает worker,
    чтобы на демо можно было в один клик показать "вот я загружаю видео,
    и ИИ уже анализирует".
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            400,
            f"Неподдерживаемый формат '{ext}'. Разрешены: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(413, f"Файл больше {MAX_UPLOAD_SIZE_MB} МБ — для демо возьми ролик покороче")
    if not contents:
        raise HTTPException(400, "Пустой файл")

    unique_suffix = uuid.uuid4().hex[:8]
    stored_name = f"{_safe_name(file.filename)}_{unique_suffix}{ext}"
    dest_path = UPLOADS_DIR / stored_name
    dest_path.write_bytes(contents)

    dest_path = _transcode_to_playable_mp4(dest_path)

    display_name = name or f"UPLOAD-{_safe_name(file.filename)}"

    source = Source(
        name=display_name,
        type=SourceType.camera,
        stream_url=str(dest_path),
        lat=lat,
        lon=lon,
        location_label=location_label or "Загруженное демо-видео",
        status=SourceStatus.inactive,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    if autostart:
        ok, message = worker_manager.start_worker(source.id, source.stream_url, source.lat, source.lon)
        if ok:
            source.status = SourceStatus.active
            db.commit()
            db.refresh(source)
        # Если worker не стартовал (например лимит одновременных источников) —
        # source всё равно создан, просто останется inactive; фронт может
        # предложить запустить вручную кнопкой "Start".

    return source


@router.post("/photo")
async def upload_demo_photo(
    file: UploadFile = File(...),
    lat: float = Form(42.9000),
    lon: float = Form(71.3667),
):
    """
    Загрузка ОДНОЙ фотографии (не видео) — ИИ анализирует один кадр и сразу
    возвращает картинку с рамками найденных проблем (ДТП/пожар/дым/яма/
    человек в опасности) + список детектов. В отличие от /uploads/video,
    не создаёт Source и не запускает pipeline/worker — фото не поток,
    анализировать его непрерывно нечего, достаточно одного прогона детектора.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise HTTPException(
            400,
            f"Неподдерживаемый формат фото '{ext}'. Разрешены: {', '.join(sorted(ALLOWED_PHOTO_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_PHOTO_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"Фото больше {MAX_PHOTO_SIZE_MB} МБ")
    if not contents:
        raise HTTPException(400, "Пустой файл")

    np_arr = np.frombuffer(contents, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Не удалось прочитать изображение — файл повреждён или не поддерживается")

    # Детектор обучен работать на уменьшенном кадре (см. INFERENCE_RESOLUTION в
    # config.py) — так же, как каждый кадр видео в pipeline_runner.py.
    inference_frame = cv2.resize(frame, INFERENCE_RESOLUTION)
    detector = get_detector()
    detections = detector.detect(inference_frame)

    annotated = draw_detections(frame.copy(), detections)

    unique_suffix = uuid.uuid4().hex[:8]
    out_name = f"photo_{unique_suffix}.jpg"
    out_path = PHOTOS_DIR / out_name
    cv2.imwrite(str(out_path), annotated)

    return {
        "photo_url": f"/photos/{out_name}",
        "lat": lat,
        "lon": lon,
        "detections": [
            {
                "class": d["class"],
                "label_ru": LABELS_RU.get(d["class"], d["class"]),
                "confidence": d["confidence"],
            }
            for d in detections
        ],
        "problems_found": len(detections) > 0,
    }


@router.delete("/video/{source_id}")
def delete_uploaded_video(source_id: int, db: Session = Depends(get_db)):
    """Останавливает worker (если активен) и удаляет и Source, и сам файл с диска."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source не найден")

    if worker_manager.is_active(source_id):
        worker_manager.stop_worker(source_id)
        time.sleep(0.1)

    file_path = Path(source.stream_url)
    if file_path.exists() and file_path.is_relative_to(UPLOADS_DIR):
        file_path.unlink(missing_ok=True)

    db.delete(source)
    db.commit()
    return {"status": "deleted", "source_id": source_id}
