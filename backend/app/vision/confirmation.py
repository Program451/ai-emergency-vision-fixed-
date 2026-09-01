

import time
from collections import deque

from app.config import (
    CONFIRMATION_WINDOW,
    CONFIRMATION_FRAMES,
    MIN_CONFIDENCE,
    COOLDOWN_SECONDS,
)


class ConfirmationEngine:
    def __init__(self):
        # source_id -> deque[ list[detections для этого кадра] ]
        self._buffers: dict[int, deque] = {}
        # (source_id, event_type) -> timestamp последнего подтверждённого события
        self._last_confirmed: dict[tuple, float] = {}

    def _buffer_for(self, source_id: int) -> deque:
        if source_id not in self._buffers:
            self._buffers[source_id] = deque(maxlen=CONFIRMATION_WINDOW)
        return self._buffers[source_id]

    def push_frame(self, source_id: int, detections: list) -> list:
        """
        Добавляет "сырые" детекты одного кадра в буфер source'а и возвращает
        список НОВЫХ подтверждённых событий (обычно 0 или 1 за вызов).

        Каждый подтверждённый событие — dict:
        {
            "event_type": "car_accident",
            "confidence": 0.87,          # среднее по подтверждающим кадрам
            "people_detected": 2,        # max по буферу
            "smoke_detected": True,      # встречалось в буфере
        }
        """
        buf = self._buffer_for(source_id)
        buf.append([d for d in detections if d["confidence"] >= MIN_CONFIDENCE])

        confirmed_events = []

        # Событийные классы (то, что реально пишем в incidents), а не car/person —
        # они только вспомогательные сигналы для people_detected/smoke_detected.
        event_classes = {"car_accident", "fire", "smoke", "person_fallen", "pothole"}

        seen_types = {d["class"] for frame_dets in buf for d in frame_dets if d["class"] in event_classes}

        for event_type in seen_types:
            frames_with_event = [
                [d for d in frame_dets if d["class"] == event_type] for frame_dets in buf
            ]
            count = sum(1 for f in frames_with_event if len(f) > 0)

            if count < CONFIRMATION_FRAMES:
                continue

            cooldown_key = (source_id, event_type)
            last_time = self._last_confirmed.get(cooldown_key, 0)
            if time.time() - last_time < COOLDOWN_SECONDS:
                continue  # ещё в cooldown — не дублируем incident

            confidences = [d["confidence"] for f in frames_with_event for d in f]
            avg_confidence = round(sum(confidences) / len(confidences), 3)

            people_detected = max(
                (sum(1 for d in frame_dets if d["class"] == "person") for frame_dets in buf),
                default=0,
            )
            smoke_detected = any(
                any(d["class"] == "smoke" for d in frame_dets) for frame_dets in buf
            )

            confirmed_events.append(
                {
                    "event_type": event_type,
                    "confidence": avg_confidence,
                    "people_detected": people_detected,
                    "smoke_detected": smoke_detected,
                }
            )
            self._last_confirmed[cooldown_key] = time.time()

        return confirmed_events

    def reset(self, source_id: int):
        """Очистить буфер источника (например, при остановке worker'а)."""
        self._buffers.pop(source_id, None)
