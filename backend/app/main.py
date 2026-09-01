
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX, SNAPSHOTS_DIR, UPLOADS_DIR, PHOTOS_DIR
from app.database import init_db
from app.api import sources, incidents, simulation, websocket, uploads
from app.api.ws_manager import manager as ws_manager

app = FastAPI(title="AI Emergency Vision API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздаём снапшоты как статику: GET /snapshots/{source_id}.jpg
# (pipeline_runner.py пишет их туда раз в SNAPSHOT_INTERVAL_SECONDS)
app.mount("/snapshots", StaticFiles(directory=str(SNAPSHOTS_DIR)), name="snapshots")

# Раздаём сами загруженные видео как статику: GET /uploads/{имя_файла}
# Нужно, чтобы можно было открыть/скачать оригинал загруженного видео
# напрямую (например для проверки, что файл реально сохранился и играет).
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Раздаём фото с нарисованными рамками (см. api/uploads.py:/uploads/photo)
app.mount("/photos", StaticFiles(directory=str(PHOTOS_DIR)), name="photos")

app.include_router(sources.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(websocket.router)  # WS без /api — фронт стучится на /ws/incidents напрямую


@app.on_event("startup")
def on_startup():
    init_db()
    # pipeline_runner работает в отдельных threading.Thread и broadcast'ит
    # через run_coroutine_threadsafe — ws_manager должен знать про текущий
    # event loop, чтобы это работало (см. api/ws_manager.py).
    ws_manager.set_loop(asyncio.get_event_loop())


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-emergency-vision-backend"}
