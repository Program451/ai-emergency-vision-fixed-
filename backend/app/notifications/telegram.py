

import httpx

from app.config import TELEGRAM_BOTS, TELEGRAM_SERVICE_FALLBACK

EVENT_LABELS_RU = {
    "car_accident": "ДТП",
    "fire": "ПОЖАР",
    "smoke": "ДЫМ",
    "person_fallen": "ПАДЕНИЕ ЧЕЛОВЕКА",
    "pothole": "ЯМА НА ДОРОГЕ",
}


def format_message(incident: dict) -> str:
    event_label = EVENT_LABELS_RU.get(incident["event_type"], incident["event_type"])
    return (
        f"🚨 EVENT #{incident['id']} — {event_label}\n"
        f"Severity: {incident['severity']}\n"
        f"Служба: {incident['service']}\n"
        f"Координаты: {incident['lat']}, {incident['lon']}\n"
        f"Confidence: {round(incident['confidence'] * 100)}%\n"
        f"{incident.get('operator_message', '')}"
    )


def _resolve_bot(service: str) -> dict:
    """Служба -> {token, chat_id}. Службы без своего бота маршрутизируются по fallback-карте."""
    routed_service = TELEGRAM_SERVICE_FALLBACK.get(service, service)
    return TELEGRAM_BOTS.get(routed_service, {"token": "", "chat_id": ""})


def send_incident_notification(incident: dict) -> bool:
    """Возвращает True, если сообщение реально отправлено в Telegram-бот нужной службы."""
    message = format_message(incident)
    bot = _resolve_bot(incident["service"])
    token, chat_id = bot["token"], bot["chat_id"]

    if not token or not chat_id:
        print(f"[TELEGRAM disabled for service={incident['service']} — would send]\n{message}")
        return False

    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=5,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        # Telegram недоступен — не роняем pipeline, просто логируем.
        print(f"[TELEGRAM ERROR service={incident['service']}] {e}\n{message}")
        return False
