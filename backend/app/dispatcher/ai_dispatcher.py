
import json

import httpx

from app.config import (
    LLM_ENABLED,
    GROQ_API_KEY,
    GROQ_API_URL,
    GROQ_MODEL,
    LLM_TIMEOUT_SECONDS,
    LOW_CONFIDENCE_THRESHOLD,
)
from app.dispatcher.prompts import SYSTEM_PROMPT, build_user_prompt



_SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _base_rule(event_type: str, people_detected: int, smoke_detected: bool, confidence: float):
    if event_type == "car_accident":
        if people_detected >= 1:
            return "CRITICAL", "EMERGENCY_MEDICAL"
        return "HIGH", "POLICE"

    if event_type == "fire":
        return "CRITICAL", "FIRE_DEPARTMENT"

    if event_type == "smoke":
        return "MEDIUM", "FIRE_DEPARTMENT"

    if event_type == "person_fallen":
        if confidence >= 0.8:
            return "HIGH", "EMERGENCY_MEDICAL"
        return "MEDIUM", "EMERGENCY_MEDICAL"

    if event_type == "pothole":
        return "LOW", "ROAD_MAINTENANCE"

    # Неизвестный тип — безопасный дефолт
    return "MEDIUM", "POLICE"


def _downgrade(severity: str) -> str:
    idx = _SEVERITY_ORDER.index(severity)
    return _SEVERITY_ORDER[max(0, idx - 1)]


def _template_texts(event_type: str, severity: str, service: str) -> tuple[str, str]:
    """Шаблонный fallback — 100% надёжен, не зависит от сети."""
    reason = f"Событие '{event_type}' подтверждено системой с уровнем опасности {severity}."
    operator_message = f"Рекомендуется направить: {service}. Подтвердите происшествие и передайте в службу."
    return reason, operator_message


def _try_groq_rewrite(event_type, severity, service, confidence, people_detected, smoke_detected):
    """Возвращает (reason, operator_message) от Groq, либо None при любой ошибке/недоступности."""
    if not LLM_ENABLED:
        return None

    try:
        response = httpx.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_user_prompt(
                            event_type, severity, service, confidence, people_detected, smoke_detected
                        ),
                    },
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        reason = parsed.get("reason")
        operator_message = parsed.get("operator_message")
        if not reason or not operator_message:
            return None
        return reason, operator_message
    except Exception:
        # Сеть недоступна / таймаут / неожиданный формат — тихо падаем на шаблон.
        # Это осознанное решение: pipeline никогда не должен упасть из-за LLM.
        return None


def dispatch(event: str, confidence: float, location: dict, people_detected: int = 0, smoke_detected: bool = False) -> dict:
    """
    Главная функция модуля. Вход/выход — строго тот JSON-формат, что в ТЗ.

    Вход (по сути): {"event": ..., "confidence": ..., "location": {...},
                      "people_detected": ..., "smoke_detected": ...}
    Выход: {"severity": ..., "service": ..., "reason": ..., "operator_message": ...}
    """
    severity, service = _base_rule(event, people_detected, smoke_detected, confidence)

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        severity = _downgrade(severity)

    groq_result = _try_groq_rewrite(event, severity, service, confidence, people_detected, smoke_detected)
    if groq_result:
        reason, operator_message = groq_result
    else:
        reason, operator_message = _template_texts(event, severity, service)

    return {
        "severity": severity,
        "service": service,
        "reason": reason,
        "operator_message": operator_message,
    }
