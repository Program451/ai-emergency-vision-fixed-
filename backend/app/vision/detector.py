

import random

from app.config import (
    USE_MOCK_DETECTOR,
    COCO_MODEL_PATH,
    CUSTOM_MODEL_PATH,
    COCO_CLASS_MAP,
    CUSTOM_CLASS_MAP,
    MIN_CONFIDENCE,
)


class Detection(dict):
    """Просто dict с удобным доступом — {"class": ..., "confidence": ..., "bbox": [...]}"""


class BaseDetector:
    def detect(self, frame) -> list:
        raise NotImplementedError


class MockDetector(BaseDetector):
    """
    Имитирует детект без реальной модели. Логика: каждый вызов с некоторой
    вероятностью "видит" одно из событий с правдоподобным confidence — этого
    достаточно, чтобы Confirmation Engine реально накапливал подтверждения
    и создавал incidents, как в проде.

    Используется ТОЛЬКО пока custom_model.pt ещё не обучена (см. config.py).
    """

    def __init__(self, target_event=None):
        """
        target_event: если задан (Simulation Mode) — детектор почти всегда
        "видит" именно это событие с высокой confidence, чтобы демо было
        предсказуемым, а не зависело от генератора случайных чисел.
        """
        self._call_count = 0
        self.target_event = target_event

    def detect(self, frame) -> list:
        self._call_count += 1
        detections = []

        if self.target_event:
            # Разогрев: первые несколько кадров — низкая/средняя confidence
            # (имитация "система присматривается"), дальше — уверенный детект.
            # Это даёт на демо реалистичную картину роста confidence на экране.
            warm = min(0.5 + self._call_count * 0.08, 0.97)
            detections.append({"class": self.target_event, "confidence": round(warm, 2), "bbox": [140, 120, 320, 300]})
            if self.target_event == "car_accident" and random.random() < 0.7:
                detections.append({"class": "person", "confidence": round(random.uniform(0.6, 0.9), 2), "bbox": [50, 50, 150, 250]})
                detections.append({"class": "car", "confidence": round(random.uniform(0.7, 0.95), 2), "bbox": [100, 100, 300, 220]})
            if self.target_event == "fire" and random.random() < 0.6:
                detections.append({"class": "smoke", "confidence": round(random.uniform(0.6, 0.9), 2), "bbox": [80, 40, 260, 180]})
            return detections

        # Без target_event (обычный источник камера/дрон без сценария) —
        # редкий случайный шум, просто чтобы pipeline не был совсем пустым.
        if random.random() < 0.4:
            detections.append({"class": "person", "confidence": round(random.uniform(0.6, 0.95), 2), "bbox": [50, 50, 150, 250]})
        if random.random() < 0.5:
            detections.append({"class": "car", "confidence": round(random.uniform(0.6, 0.95), 2), "bbox": [100, 100, 300, 220]})

        return detections


class RealDetector(BaseDetector):
    """Настоящий YOLO-инференс. Требует ultralytics и веса моделей на диске."""

    def __init__(self):
        from ultralytics import YOLO  # импорт внутри, чтобы MockDetector не тянул зависимость зря

        self.coco_model = YOLO(COCO_MODEL_PATH)
        self.custom_model = YOLO(CUSTOM_MODEL_PATH)

    def detect(self, frame) -> list:
        detections = []

        coco_result = self.coco_model.predict(frame, verbose=False)[0]
        for box in coco_result.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in COCO_CLASS_MAP:
                continue
            conf = float(box.conf[0])
            if conf < MIN_CONFIDENCE:
                continue
            detections.append(
                {
                    "class": COCO_CLASS_MAP[cls_id],
                    "confidence": round(conf, 3),
                    "bbox": [float(x) for x in box.xyxy[0].tolist()],
                }
            )

        custom_result = self.custom_model.predict(frame, verbose=False)[0]
        for box in custom_result.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in CUSTOM_CLASS_MAP:
                continue
            conf = float(box.conf[0])
            if conf < MIN_CONFIDENCE:
                continue
            detections.append(
                {
                    "class": CUSTOM_CLASS_MAP[cls_id],
                    "confidence": round(conf, 3),
                    "bbox": [float(x) for x in box.xyxy[0].tolist()],
                }
            )

        return detections


def get_detector(target_event=None) -> BaseDetector:
    """
    Фабрика — вызывать один раз на воркер (загрузка модели не бесплатна).
    target_event используется только MockDetector'ом (Simulation Mode);
    RealDetector его игнорирует — там событие определяется реальной моделью.
    """
    if USE_MOCK_DETECTOR:
        return MockDetector(target_event=target_event)
    return RealDetector()
