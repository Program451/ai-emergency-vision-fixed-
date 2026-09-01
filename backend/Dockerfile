FROM python:3.11-slim

# Системные зависимости для OpenCV (libGL и т.д.) + ffmpeg.
# ffmpeg добавлен, чтобы конвертировать ЛЮБОЙ загруженный видеофайл
# (.mov/.avi/.mkv/битые mp4 с телефона или дрона) в предсказуемый
# H.264/AAC mp4 — иначе часть видео не открывалась через cv2.VideoCapture
# (у opencv-python-headless урезанная сборка ffmpeg внутри, без части кодеков).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
