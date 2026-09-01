
import cv2

from app.config import INFERENCE_RESOLUTION

LABELS_RU = {
    "car_accident": "ДТП", "fire": "ПОЖАР", "smoke": "ДЫМ",
    "person_fallen": "ЧЕЛОВЕК В ОПАСНОСТИ", "pothole": "ЯМА",
    "person": "ЧЕЛОВЕК", "car": "МАШИНА",
}


def draw_detections(frame, detections: list, bbox_in_inference_resolution: bool = True):

    if not detections:
        return frame

    fh, fw = frame.shape[:2]
    if bbox_in_inference_resolution:
        iw, ih = INFERENCE_RESOLUTION
        sx, sy = fw / iw, fh / ih
    else:
        sx, sy = 1.0, 1.0

    for det in detections:
        bbox = det.get("bbox")
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        x1, x2 = int(x1 * sx), int(x2 * sx)
        y1, y2 = int(y1 * sy), int(y2 * sy)

        label_ru = LABELS_RU.get(det["class"], det["class"])
        conf_pct = round(det.get("confidence", 0) * 100)
        color = (0, 0, 255)  # BGR — красный, хорошо видно на любом фоне

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        text = f"{label_ru} {conf_pct}%"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 10)), (x1 + tw + 10, y1), color, -1)
        cv2.putText(frame, text, (x1 + 5, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame
