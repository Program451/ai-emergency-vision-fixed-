
import os
from pathlib import Path

from dotenv import load_dotenv

# Подхватываем backend/.env при локальном запуске (run.py / start-dev.sh).
# В Docker переменные и так приходят через env_file в docker-compose.yml —
# load_dotenv() в этом случае просто ничего не находит и не мешает.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
SAMPLE_VIDEOS_DIR = DATA_DIR / "sample_videos"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
MODELS_WEIGHTS_DIR = BASE_DIR / "models_weights"
# Видео, загруженные вручную через Dashboard ("Upload demo video") — временные,
# живут до перезапуска source'а/контейнера, для показа комиссии на демо.
UPLOADS_DIR = DATA_DIR / "uploads"

DATABASE_URL = f"sqlite:///{DATA_DIR / 'incidents.db'}"

SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Разрешённые расширения для загрузки демо-видео + лимит размера (защита демо-ноутбука).
ALLOWED_UPLOAD_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_UPLOAD_SIZE_MB = 300

# Загрузка одиночных фото (не видео) — ИИ анализирует один кадр и сразу
# возвращает картинку с рамками найденных проблем, без запуска pipeline/worker.
ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_SIZE_MB = 25
PHOTOS_DIR = DATA_DIR / "photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Модели YOLO
# ---------------------------------------------------------------------------

# Базовая COCO-модель — даёт car, person "из коробки".
COCO_MODEL_PATH = str(MODELS_WEIGHTS_DIR / "yolov8n.pt")

# Кастомная модель (обучена на Roboflow под наши классы).
# Пока файла нет — detector.py работает в mock-режиме.
CUSTOM_MODEL_PATH = str(MODELS_WEIGHTS_DIR / "custom_model.pt")

# Классы кастомной модели -> внутренний event_type системы.
# Сверено напрямую с весами best.pt (model.names внутри чекпоинта):
#   0: grass_burning, 1: car_accident, 2: smoke, 3: fire,
#   4: suicide, 5: person_in_distress, 6: pits
# Обученная модель понимает 7 классов, а не 5 из первоначального ТЗ:
# добавлены grass_burning ("горение травы" — маппим в fire) и
# suicide/person_in_distress (человек в опасности — маппим в person_fallen,
# это по-прежнему EMERGENCY_MEDICAL по rule-based таблице ai_dispatcher.py).
CUSTOM_CLASS_MAP = {
    0: "fire",           # grass_burning -> fire (тот же service: FIRE_DEPARTMENT)
    1: "car_accident",
    2: "smoke",
    3: "fire",
    4: "person_fallen",  # suicide -> максимально осторожный event_type,
                          # severity/service всё равно решает rule-based таблица
    5: "person_fallen",  # person_in_distress
    6: "pothole",        # pits
}

# Классы COCO-модели, которые нас интересуют (остальные игнорируем).
COCO_CLASS_MAP = {
    2: "car",     # COCO id=2 -> car
    0: "person",  # COCO id=0 -> person
}

# Если кастомной модели ещё нет на диске — используем DetectorMock,
# чтобы весь pipeline можно было разрабатывать и тестировать уже сейчас.
USE_MOCK_DETECTOR = not os.path.exists(CUSTOM_MODEL_PATH)

# ---------------------------------------------------------------------------
# Vision / инференс
# ---------------------------------------------------------------------------

# Обрабатывать не каждый кадр, а раз в N кадров — критично для CPU-демо.
FRAME_SKIP = 5

# Даунскейл кадра перед инференсом (width, height) — сильно ускоряет YOLO на CPU.
INFERENCE_RESOLUTION = (480, 480)

# Порог доверия к одному "сырому" детекту на одном кадре.
MIN_CONFIDENCE = 0.5

# ---------------------------------------------------------------------------
# Confirmation logic (защита от ложных срабатываний)
# ---------------------------------------------------------------------------

# Размер скользящего окна (в обработанных кадрах, т.е. с учётом FRAME_SKIP).
CONFIRMATION_WINDOW = 10

# Сколько кадров из окна должны содержать событие, чтобы считать его подтверждённым.
CONFIRMATION_FRAMES = 5

# После подтверждённого события того же типа с того же источника —
# не создавать новый incident, пока не пройдёт cooldown (секунды).
COOLDOWN_SECONDS = 60

# ---------------------------------------------------------------------------
# Workers (multi-source)
# ---------------------------------------------------------------------------

# Сколько источников можно обрабатывать одновременно.
# Ограничение осознанное — демо крутится на CPU-ноутбуке.
# Поднято с 2 до 4: после бага в worker_manager (слоты не освобождались,
# когда видео доигрывало само) даже лимит "2" по факту давал 0 после
# первых пары роликов. Теперь слоты освобождаются корректно, так что
# можно держать больше источников одновременно (камера + бот-видео + др.).
MAX_CONCURRENT_WORKERS = int(os.environ.get("MAX_CONCURRENT_WORKERS", "4"))

# Как часто worker обновляет "живой" снапшот источника для Dashboard (секунды).
SNAPSHOT_INTERVAL_SECONDS = 1.0

# ---------------------------------------------------------------------------
# AI Dispatcher
# ---------------------------------------------------------------------------

# Rule-based всегда работает и никогда не зависит от сети.
# LLM (Groq) используется ТОЛЬКО для рерайта reason/operator_message,
# никогда не участвует в определении severity/service — так демо не может
# сломаться из-за плохого Wi-Fi/недоступности API на хакатоне.
# Если GROQ_API_KEY не задан или запрос упал — автоматический fallback
# на шаблонный текст (см. dispatcher/ai_dispatcher.py).
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
LLM_ENABLED = bool(GROQ_API_KEY)
LLM_TIMEOUT_SECONDS = 4  # короткий таймаут — не задерживаем pipeline на демо

# Если итоговая confidence события ниже этого порога — severity понижается
# на один уровень относительно базового правила.
LOW_CONFIDENCE_THRESHOLD = 0.6

VALID_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VALID_SERVICES = ["EMERGENCY_MEDICAL", "FIRE_DEPARTMENT", "POLICE", "ROAD_MAINTENANCE"]
VALID_EVENT_TYPES = ["car_accident", "fire", "smoke", "person_fallen", "pothole"]
VALID_STATUSES = ["NEW", "CONFIRMED", "SENT", "RESOLVED"]

# ---------------------------------------------------------------------------
# Telegram — отдельный бот на каждую службу.
# Событие маршрутизируется по incident.service (см. dispatcher/ai_dispatcher.py):
#   POLICE            -> TELEGRAM_BOT_TOKEN_POLICE
#   EMERGENCY_MEDICAL  -> TELEGRAM_BOT_TOKEN_MEDICAL
#   FIRE_DEPARTMENT    -> TELEGRAM_BOT_TOKEN_FIRE
#   ROAD_MAINTENANCE   -> шлём в POLICE-бот как дефолт (нет отдельной службы под ямы)
# Если для службы не задан токен/chat_id — просто логируем в консоль, pipeline не падает.
# ---------------------------------------------------------------------------

TELEGRAM_BOTS = {
    "POLICE": {
        "token": os.environ.get("TELEGRAM_BOT_TOKEN_POLICE", ""),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID_POLICE", ""),
    },
    "EMERGENCY_MEDICAL": {
        "token": os.environ.get("TELEGRAM_BOT_TOKEN_MEDICAL", ""),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID_MEDICAL", ""),
    },
    "FIRE_DEPARTMENT": {
        "token": os.environ.get("TELEGRAM_BOT_TOKEN_FIRE", ""),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID_FIRE", ""),
    },
}
# ROAD_MAINTENANCE не имеет своей службы/бота — по умолчанию маршрутизируется в POLICE.
TELEGRAM_SERVICE_FALLBACK = {
    "ROAD_MAINTENANCE": "POLICE",
}

# ---------------------------------------------------------------------------
# Simulation Mode — готовые сценарии для демо
# ---------------------------------------------------------------------------

SIMULATION_SCENARIOS = {
    "car_accident": {
        "label": "ДТП",
        "event_type": "car_accident",
        "video_file": str(SAMPLE_VIDEOS_DIR / "car_accident.mp4"),
        "lat": 42.9000,
        "lon": 71.3667,  # демо-координаты в Таразе
    },
    "fire": {
        "label": "ПОЖАР",
        "event_type": "fire",
        "video_file": str(SAMPLE_VIDEOS_DIR / "fire.mp4"),
        "lat": 42.9010,
        "lon": 71.3700,
    },
    "fall": {
        "label": "ПАДЕНИЕ",
        "event_type": "person_fallen",  # ключ сценария "fall", но event_type в системе — "person_fallen"
        "video_file": str(SAMPLE_VIDEOS_DIR / "fall.mp4"),
        "lat": 42.8990,
        "lon": 71.3650,
    },
    "pothole": {
        "label": "ЯМА",
        "event_type": "pothole",
        "video_file": str(SAMPLE_VIDEOS_DIR / "pothole.mp4"),
        "lat": 42.9020,
        "lon": 71.3680,
    },
}

# ---------------------------------------------------------------------------
# CORS (frontend dev server)
# ---------------------------------------------------------------------------

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # БАГФИКС: раньше тут не было порта фронта из docker-compose.yml (3000),
    # поэтому при запуске через docker-compose браузер молча блокировал
    # все запросы к backend (CORS), и фронт выглядел "сломанным" —
    # источники/видео/боты не грузились, хотя backend работал нормально.
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Разрешаем доступ и с телефона/другого ПК в той же Wi-Fi сети (например,
# зайти на дашборд по http://192.168.x.x:3000 — нужно для гео и OBS
# с другого устройства). Домашние/офисные диапазоны 192.168.*, 10.*, 172.16-31.*
CORS_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$"
