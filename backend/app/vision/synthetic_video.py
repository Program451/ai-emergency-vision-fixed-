

import os

import cv2
import numpy as np


def ensure_placeholder_video(path: str, label: str, seconds: int = 8, fps: int = 15, size=(640, 480)):
    if os.path.exists(path):
        return  # реальное (или уже сгенерированное) видео уже на месте

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, size)

    total_frames = seconds * fps
    for i in range(total_frames):
        # Плавно меняющийся цвет фона + текст с названием сценария — просто
        # чтобы было видно на демо, что видео реально проигрывается.
        hue = int(180 * (i / total_frames))
        color_frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        color_hsv = np.uint8([[[hue, 120, 180]]])
        bgr = cv2.cvtColor(color_hsv, cv2.COLOR_HSV2BGR)[0][0]
        color_frame[:] = bgr

        cv2.putText(
            color_frame, f"SIMULATION: {label}", (30, size[1] // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA,
        )
        cv2.putText(
            color_frame, f"frame {i}/{total_frames}", (30, size[1] // 2 + 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA,
        )
        writer.write(color_frame)

    writer.release()
    print(f"[synthetic_video] сгенерирован плейсхолдер: {path}")
