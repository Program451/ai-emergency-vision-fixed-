# AI Emergency Vision

Платформа компьютерного зрения для мониторинга городских камер и дронов:
обнаружение ДТП, пожара/дыма, падения человека и ям на дороге, с
формированием структурированного происшествия для оператора.

```
ВИДЕО → YOLO/OpenCV → detection → confirmation → AI Dispatcher →
→ Dashboard оператора + Telegram-уведомление + журнал происшествий
```

## Быстрый запуск (Docker — рекомендуется)

```bash
docker compose up --build
```

- Frontend (Dashboard): http://localhost:3000
- Backend API + Swagger docs: http://localhost:8000/docs

## Быстрый запуск (без Docker, для разработки)

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # заполнить GROQ_API_KEY / TELEGRAM_* при наличии

# frontend
cd ../frontend
npm install

# из корня проекта — поднимает оба сразу
cd ..
./start-dev.sh
```

Backend: http://localhost:8000 · Frontend: http://localhost:5173

## Структура проекта

```
ai-emergency-vision/
├── backend/
│   ├── app/
│   │   ├── config.py          — ВСЕ параметры pipeline (пороги, пути, ключи)
│   │   ├── main.py            — FastAPI entrypoint
│   │   ├── database.py        — SQLAlchemy (SQLite)
│   │   ├── models/            — ORM (Source, Incident) + Pydantic-схемы
│   │   ├── vision/
│   │   │   ├── video_reader.py    — чтение видео (файл/RTSP/webcam)
│   │   │   ├── detector.py        — YOLO-обёртка (Mock, пока нет custom-модели)
│   │   │   ├── confirmation.py    — защита от ложных срабатываний
│   │   │   └── synthetic_video.py — автогенерация demo-видео для Simulation Mode
│   │   ├── dispatcher/
│   │   │   ├── ai_dispatcher.py   — severity/service (rule-based) + Groq-рерайт текста
│   │   │   └── prompts.py
│   │   ├── notifications/telegram.py
│   │   ├── services/
│   │   │   ├── pipeline_runner.py — склейка всего pipeline (один source)
│   │   │   └── worker_manager.py  — управление несколькими source одновременно
│   │   └── api/
│   │       ├── sources.py     — GET/POST /sources, start/stop
│   │       ├── incidents.py   — GET /incidents, PATCH статус
│   │       ├── simulation.py  — POST /simulate/{scenario}
│   │       ├── uploads.py     — POST /uploads/video (демо-загрузка ролика)
│   │       └── websocket.py   — WS /ws/incidents (realtime push на Dashboard)
│   ├── data/
│   │   ├── incidents.db       — создаётся автоматически при первом запуске
│   │   ├── sample_videos/     — сюда положить реальные demo-видео
│   │   ├── snapshots/         — live-кадры источников (для Dashboard)
│   │   └── uploads/           — временные видео, загруженные через Dashboard
│   └── models_weights/        — custom_model.pt (уже подключена, см. ниже)
│
└── frontend/
    ├── src/
    │   ├── components/        — TopBar, SideNav, SourcesList, SimulationPanel,
    │   │                         UploadDemoPanel (upload + OBS/RTSP),
    │   │                         LiveCameraPanel, MapView, IncidentCard/Panel, IncidentLog
    │   ├── pages/Dashboard.jsx — главная страница, real API + WebSocket
    │   ├── api/client.js      — обёртка над backend Event API
    │   └── mock/mockData.js   — fallback-данные, если backend не запущен
    └── tailwind.config.js     — цветовая схема (EOC dark theme)
```

## Как подключить то, что придёт позже

### Обученная YOLO-модель (`custom_model.pt`) — УЖЕ ПОДКЛЮЧЕНА

Файл лежит в `backend/models_weights/custom_model.pt`. `USE_MOCK_DETECTOR`
сам определяет, что файл есть — `detector.py` работает в `RealDetector`.

⚠️ Модель обучена на **7 классах**, не на 5 из исходного ТЗ. Сверено
напрямую с весами (`model.names` внутри чекпоинта):
```
0: grass_burning   1: car_accident   2: smoke   3: fire
4: suicide         5: person_in_distress   6: pits
```
`CUSTOM_CLASS_MAP` в `config.py` уже перемапплен под них:
`grass_burning`/`fire` → `fire` (одна и та же служба — пожарные),
`suicide`/`person_in_distress` → `person_fallen` (человек в опасности,
едет EMERGENCY_MEDICAL — см. rule-based таблицу в `ai_dispatcher.py`),
`pits` → `pothole`. Если модель переобучите — проверьте маппинг заново,
он привязан именно к текущему `best.pt`.

Также при первом запуске `RealDetector` скачивает базовую COCO-модель
`yolov8n.pt` (~6 МБ) через ultralytics — нужен интернет один раз при
первом старте backend, дальше файл кэшируется в `models_weights/`.

### GROQ_API_KEY (LLM-рерайт текста происшествия) — УЖЕ ПОДКЛЮЧЕН

Ключ уже в `backend/.env` (`GROQ_API_KEY`). Без него система работает на
rule-based шаблонных текстах — pipeline никогда не падает из-за
отсутствия/недоступности Groq.

### Telegram-боты (мультибот-роутинг по службам) — УЖЕ ПОДКЛЮЧЕНЫ

Каждая служба шлёт уведомления через свой бот — см. `TELEGRAM_BOTS` в
`config.py` и `notifications/telegram.py`:
```
TELEGRAM_BOT_TOKEN_POLICE / TELEGRAM_CHAT_ID_POLICE     — POLICE, ROAD_MAINTENANCE (fallback)
TELEGRAM_BOT_TOKEN_MEDICAL / TELEGRAM_CHAT_ID_MEDICAL   — EMERGENCY_MEDICAL
TELEGRAM_BOT_TOKEN_FIRE / TELEGRAM_CHAT_ID_FIRE         — FIRE_DEPARTMENT
```
Токены ботов уже в `.env`. **`TELEGRAM_CHAT_ID_*` пока пустые** —
добавьте каждого бота в нужный чат/группу, затем получите chat_id
(проще всего: написать боту в чат и открыть
`https://api.telegram.org/bot<TOKEN>/getUpdates`) и впишите в `.env`.
Пока chat_id не заполнен — уведомления просто логируются в консоль
backend, pipeline не падает.

### Живые источники: OBS / веб-камера / RTSP-камера или дрон

На Dashboard, вкладка **"OBS / Камера / RTSP"** в панели слева:
- **OBS Virtual Camera**: в OBS → Инструменты → Запустить виртуальную
  камеру. Она появляется в системе как обычная веб-камера — в поле
  адреса просто впиши индекс `0` (или `1`, если это не первая камера
  в системе). Через OBS так же можно завести видео с телефона или
  дрона (как источник видео в самой OBS) — для backend это будет
  неотличимо от обычной веб-камеры.
- **RTSP-камера/дрон с FPV-трансляцией**: `rtsp://логин:пароль@ip:554/поток`.

### Загрузка демо-видео (для показа на защите)

На той же панели, вкладка **"Загрузить видео"** — drag-and-drop или
клик, поддерживаются MP4/MOV/AVI/MKV/WEBM до 300 МБ. Видео сохраняется
во временную папку `backend/data/uploads/` (не коммитится в git),
автоматически создаёт Source и сразу запускает pipeline — можно за
несколько секунд показать комиссии "вот я загружаю ролик, а вот ИИ
уже находит на нём событие".

### Реальные demo-видео для Simulation Mode

Положить файлы в `backend/data/sample_videos/`:
```
car_accident.mp4
fire.mp4
fall.mp4
pothole.mp4
```
Пока файлов нет — `synthetic_video.py` автоматически генерирует
плейсхолдер-ролик при первом запуске сценария, чтобы Simulation Mode
работал уже сейчас, на MockDetector.

## Проверка, что всё работает (smoke test)

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/simulate/car_accident
sleep 5
curl http://localhost:8000/api/incidents
```
Должен появиться incident с `event_type: car_accident`, `severity: CRITICAL`,
`service: EMERGENCY_MEDICAL` (если MockDetector "увидел" людей в кадре).

## Ключевые архитектурные решения (кратко)

- **severity/service всегда rule-based** — LLM (Groq) только переписывает
  текст `reason`/`operator_message`, никогда не участвует в принятии
  решения. Демо не может сломаться из-за плохого Wi-Fi.
- **Координаты берутся из Source Registry**, не вычисляются по кадру —
  надёжнее для MVP, чем geo-estimation по картинке.
- **Confirmation Engine** — событие подтверждается, только если
  встречается в ≥5 из последних 10 обработанных кадров (настраивается
  в `config.py`: `CONFIRMATION_WINDOW`, `CONFIRMATION_FRAMES`).
- **Multi-source**: `WorkerManager` запускает pipeline каждого source в
  отдельном потоке, лимит `MAX_CONCURRENT_WORKERS=2` (безопасно для
  CPU-демо на ноутбуке без GPU).
- **Live-видео на Dashboard** — не WebRTC, а poll обновляющегося JPEG-
  снапшота раз в секунду (`SNAPSHOT_INTERVAL_SECONDS`). Для демо неотличимо
  от настоящего стрима, разработка в разы быстрее.
#   a i - 020@89=>5  2845=85- 8A?@02;5=>-  
 