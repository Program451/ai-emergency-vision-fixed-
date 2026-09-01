

import cv2

from app.config import FRAME_SKIP, INFERENCE_RESOLUTION


class VideoReader:
    def __init__(self, source_url: str):
        """
        source_url:
          - путь к файлу (Simulation Mode, тестовое видео с дрона на SD-карте)
          - "0" / int-строка — локальная webcam
          - "rtsp://..." — живой поток (камера с RTSP или дрон с FPV-трансляцией)
        """
        self.source_url = source_url
        self.cap = None

    def open(self):
        # int-строка ("0", "1") -> индекс локальной камеры, иначе путь/URL как есть
        src = int(self.source_url) if self.source_url.isdigit() else self.source_url
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть источник видео: {self.source_url}")
        return self

    def frames(self):
        """Генератор кадров с учётом FRAME_SKIP и ресайза под INFERENCE_RESOLUTION."""
        if self.cap is None:
            self.open()

        frame_index = 0
        while True:
            ok, frame = self.cap.read()
            if not ok:
                break  # конец файла, либо поток оборвался

            if frame_index % FRAME_SKIP == 0:
                resized = cv2.resize(frame, INFERENCE_RESOLUTION)
                yield frame_index, resized, frame  # (индекс, кадр для YOLO, оригинальный кадр для снапшота)

            frame_index += 1

    def read_single_frame(self):
        """Для снапшотов Dashboard — просто последний доступный кадр без ресайза."""
        if self.cap is None:
            self.open()
        ok, frame = self.cap.read()
        return frame if ok else None

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
