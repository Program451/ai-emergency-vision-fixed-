import { useCallback, useRef, useState } from "react";
import { uploadDemoVideo, uploadDemoPhoto, createSource, startSource } from "../api/client.js";

// Панель для показа комиссии "вживую": загрузка видеофайла (телефон/дрон/архив),
// ЛИБО загрузка одиночного фото (ИИ анализирует один кадр и сразу возвращает
// картинку с нарисованными рамками), ЛИБО подключение живого источника —
// камера ноутбука, OBS Virtual Camera, RTSP-поток с дрона/IP-камеры.
//
// Раньше "Видео" и "Фото" были одной вкладкой с общей dropzone, и тип файла
// определялся автоматически по расширению — с виду казалось, что отдельного
// места "именно для фото" нет. Теперь это две независимые вкладки с двумя
// независимыми dropzone и своим accept на инпуте, чтобы было однозначно видно,
// куда кидать фото, а куда видео.

const TABS = [
  { key: "video", label: "Видео", icon: "movie" },
  { key: "photo", label: "Фото", icon: "photo_camera" },
  { key: "live", label: "OBS / Камера / RTSP", icon: "videocam" },
];

const VIDEO_ACCEPT = "video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,video/webm";
const PHOTO_ACCEPT = "image/jpeg,image/png,image/webp";

export default function UploadDemoPanel({ onSourceReady }) {
  const [activeTab, setActiveTab] = useState("video");

  // --- video upload state ---
  const [videoDragOver, setVideoDragOver] = useState(false);
  const [videoState, setVideoState] = useState({ status: "idle", progress: 0, error: null });
  const videoInputRef = useRef(null);

  // --- photo upload state ---
  const [photoDragOver, setPhotoDragOver] = useState(false);
  const [photoState, setPhotoState] = useState({ status: "idle", progress: 0, error: null });
  const [photoResult, setPhotoResult] = useState(null); // { photo_url, detections, problems_found }
  const photoInputRef = useRef(null);

  // --- live source form state ---
  const [liveName, setLiveName] = useState("");
  // "0" стоит по умолчанию — это индекс камеры/OBS Virtual Camera почти
  // всегда. Раньше поле было пустым, и без ввода "0" вручную кнопка
  // "Подключить" даже не давала отправить форму (см. handleConnectLive).
  const [liveUrl, setLiveUrl] = useState("0");
  const [liveBusy, setLiveBusy] = useState(false);
  const [liveError, setLiveError] = useState(null);
  const [liveLat, setLiveLat] = useState(42.9);
  const [liveLon, setLiveLon] = useState(71.3667);
  const [geoStatus, setGeoStatus] = useState("idle"); // idle | locating | done | error

  const handleUseMyLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoStatus("error");
      return;
    }
    setGeoStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLiveLat(pos.coords.latitude);
        setLiveLon(pos.coords.longitude);
        setGeoStatus("done");
      },
      () => setGeoStatus("error"),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }, []);

  const handleVideoFiles = useCallback(
    async (files) => {
      const file = files?.[0];
      if (!file) return;

      setVideoState({ status: "uploading", progress: 0, error: null });
      try {
        const source = await uploadDemoVideo(file, {
          onProgress: (pct) => setVideoState((s) => ({ ...s, progress: pct })),
        });
        setVideoState({ status: "done", progress: 100, error: null });
        onSourceReady?.(source);
        setTimeout(() => setVideoState({ status: "idle", progress: 0, error: null }), 2500);
      } catch (err) {
        setVideoState({ status: "error", progress: 0, error: err.message || "Ошибка загрузки видео" });
      }
    },
    [onSourceReady]
  );

  const handlePhotoFiles = useCallback(
    async (files) => {
      const file = files?.[0];
      if (!file) return;

      setPhotoResult(null);
      setPhotoState({ status: "uploading", progress: 0, error: null });
      try {
        const result = await uploadDemoPhoto(file, {
          lat: liveLat,
          lon: liveLon,
          onProgress: (pct) => setPhotoState((s) => ({ ...s, progress: pct })),
        });
        setPhotoState({ status: "done", progress: 100, error: null });
        setPhotoResult(result);
      } catch (err) {
        setPhotoState({ status: "error", progress: 0, error: err.message || "Ошибка загрузки фото" });
      }
    },
    [liveLat, liveLon]
  );

  const handleVideoDrop = useCallback(
    (e) => {
      e.preventDefault();
      setVideoDragOver(false);
      handleVideoFiles(e.dataTransfer.files);
    },
    [handleVideoFiles]
  );

  const handlePhotoDrop = useCallback(
    (e) => {
      e.preventDefault();
      setPhotoDragOver(false);
      handlePhotoFiles(e.dataTransfer.files);
    },
    [handlePhotoFiles]
  );

  const handleConnectLive = useCallback(async () => {
    if (!liveUrl.trim()) {
      setLiveError("Укажи адрес источника (см. подсказки ниже)");
      return;
    }
    setLiveBusy(true);
    setLiveError(null);
    try {
      const source = await createSource({
        name: liveName.trim() || "LIVE-SOURCE",
        type: "camera",
        stream_url: liveUrl.trim(),
        lat: liveLat,
        lon: liveLon,
        location_label: "Live: OBS / камера / RTSP",
      });
      await startSource(source.id);
      onSourceReady?.({ ...source, status: "active" });
      setLiveName("");
      setLiveUrl("0");
    } catch (err) {
      setLiveError(err.message || "Не удалось подключить источник");
    } finally {
      setLiveBusy(false);
    }
  }, [liveName, liveUrl, liveLat, liveLon, onSourceReady]);

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col gap-3">
      <div className="flex gap-1 border-b border-outline-variant/30 pb-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setActiveTab(t.key)}
            className={
              "flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md font-label-caps text-label-caps transition-colors " +
              (activeTab === t.key
                ? "bg-primary-fixed/15 text-primary-fixed"
                : "text-outline hover:text-on-surface-variant")
            }
          >
            <span className="material-symbols-outlined text-[16px]">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "video" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setVideoDragOver(true);
          }}
          onDragLeave={() => setVideoDragOver(false)}
          onDrop={handleVideoDrop}
          onClick={() => videoInputRef.current?.click()}
          className={
            "rounded-lg border-2 border-dashed p-5 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors text-center " +
            (videoDragOver
              ? "border-primary-fixed bg-primary-fixed/10"
              : "border-outline-variant/40 hover:border-primary-fixed/50 bg-surface-container/40")
          }
        >
          <input
            ref={videoInputRef}
            type="file"
            accept={VIDEO_ACCEPT}
            className="hidden"
            onChange={(e) => handleVideoFiles(e.target.files)}
          />

          {videoState.status === "uploading" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-primary-fixed animate-pulse">
                cloud_upload
              </span>
              <div className="w-full h-1.5 rounded-full bg-surface-container overflow-hidden">
                <div
                  className="h-full bg-primary-fixed transition-all"
                  style={{ width: `${videoState.progress}%` }}
                />
              </div>
              <span className="font-data-mono text-[10px] text-on-surface-variant">
                Загрузка… {videoState.progress}%
              </span>
            </>
          )}

          {videoState.status === "done" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-primary-fixed">check_circle</span>
              <span className="font-label-caps text-label-caps text-primary-fixed">
                Видео загружено, ИИ уже анализирует
              </span>
            </>
          )}

          {videoState.status === "error" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-error">error</span>
              <span className="font-data-mono text-[10px] text-error">{videoState.error}</span>
            </>
          )}

          {videoState.status === "idle" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-outline">movie</span>
              <span className="font-label-caps text-label-caps text-on-surface-variant">
                Перетащи видео сюда, или нажми, чтобы выбрать файл
              </span>
              <span className="font-data-mono text-[9px] text-outline">
                MP4 / MOV / AVI / MKV / WEBM, до 300 МБ
              </span>
            </>
          )}
        </div>
      )}

      {activeTab === "photo" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setPhotoDragOver(true);
          }}
          onDragLeave={() => setPhotoDragOver(false)}
          onDrop={handlePhotoDrop}
          onClick={() => photoInputRef.current?.click()}
          className={
            "rounded-lg border-2 border-dashed p-5 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors text-center " +
            (photoDragOver
              ? "border-primary-fixed bg-primary-fixed/10"
              : "border-outline-variant/40 hover:border-primary-fixed/50 bg-surface-container/40")
          }
        >
          <input
            ref={photoInputRef}
            type="file"
            accept={PHOTO_ACCEPT}
            className="hidden"
            onChange={(e) => handlePhotoFiles(e.target.files)}
          />

          {photoState.status === "uploading" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-primary-fixed animate-pulse">
                cloud_upload
              </span>
              <div className="w-full h-1.5 rounded-full bg-surface-container overflow-hidden">
                <div
                  className="h-full bg-primary-fixed transition-all"
                  style={{ width: `${photoState.progress}%` }}
                />
              </div>
              <span className="font-data-mono text-[10px] text-on-surface-variant">
                Анализирую фото… {photoState.progress}%
              </span>
            </>
          )}

          {photoState.status === "done" && photoResult && (
            <div className="w-full flex flex-col items-center gap-2">
              <img
                src={photoResult.photo_url}
                alt="Результат анализа фото"
                className="w-full rounded-lg border border-outline-variant/30"
              />
              {photoResult.problems_found ? (
                <div className="w-full flex flex-col gap-1">
                  <span className="font-label-caps text-label-caps text-error">Найдены проблемы:</span>
                  {photoResult.detections.map((d, i) => (
                    <span key={i} className="font-data-mono text-[10px] text-on-surface-variant">
                      • {d.label_ru} — {Math.round(d.confidence * 100)}%
                    </span>
                  ))}
                </div>
              ) : (
                <span className="font-label-caps text-label-caps text-primary-fixed">
                  Проблем на фото не найдено
                </span>
              )}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setPhotoResult(null);
                  setPhotoState({ status: "idle", progress: 0, error: null });
                }}
                className="font-data-mono text-[9px] text-outline hover:text-on-surface-variant underline"
              >
                Загрузить ещё
              </button>
            </div>
          )}

          {photoState.status === "error" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-error">error</span>
              <span className="font-data-mono text-[10px] text-error">{photoState.error}</span>
            </>
          )}

          {photoState.status === "idle" && (
            <>
              <span className="material-symbols-outlined text-[28px] text-outline">photo_camera</span>
              <span className="font-label-caps text-label-caps text-on-surface-variant">
                Перетащи фото сюда, или нажми, чтобы выбрать файл
              </span>
              <span className="font-data-mono text-[9px] text-outline">
                JPG / PNG / WEBP, до 25 МБ — ИИ найдёт проблемы и обведёт рамками
              </span>
            </>
          )}
        </div>
      )}

      {activeTab === "live" && (
        <div className="flex flex-col gap-2">
          <input
            type="text"
            placeholder="Название источника (например: OBS-Дрон-1)"
            value={liveName}
            onChange={(e) => setLiveName(e.target.value)}
            className="bg-surface-container rounded-lg px-3 py-2 text-[12px] text-on-surface placeholder:text-outline outline-none border border-outline-variant/20 focus:border-primary-fixed/50"
          />
          <input
            type="text"
            placeholder="0 (веб-камера) / rtsp://... / http://..."
            value={liveUrl}
            onChange={(e) => setLiveUrl(e.target.value)}
            className="bg-surface-container rounded-lg px-3 py-2 font-data-mono text-[12px] text-on-surface placeholder:text-outline outline-none border border-outline-variant/20 focus:border-primary-fixed/50"
          />
          <button
            type="button"
            onClick={handleUseMyLocation}
            className="flex items-center justify-center gap-1.5 rounded-lg py-1.5 px-3 bg-surface-container hover:bg-surface-container-high text-on-surface-variant font-label-caps text-label-caps transition-colors"
          >
            <span className="material-symbols-outlined text-[15px]">my_location</span>
            {geoStatus === "locating"
              ? "Определяю..."
              : geoStatus === "done"
                ? `Гео: ${liveLat.toFixed(4)}, ${liveLon.toFixed(4)}`
                : "Использовать моё местоположение"}
          </button>
          {geoStatus === "error" && (
            <span className="font-data-mono text-[9px] text-error">
              Не удалось получить геолокацию — браузер попросит разрешение, разреши доступ
            </span>
          )}

          {liveError && <span className="font-data-mono text-[10px] text-error">{liveError}</span>}
          <button
            onClick={handleConnectLive}
            disabled={liveBusy}
            className="rounded-lg py-2 px-3 bg-primary-fixed/15 hover:bg-primary-fixed/25 text-primary-fixed font-label-caps text-label-caps font-bold transition-colors disabled:opacity-50"
          >
            {liveBusy ? "Подключение..." : "Подключить и запустить"}
          </button>

          <div className="mt-1 flex flex-col gap-1 font-data-mono text-[9px] text-outline leading-relaxed">
            <span>• Поле выше уже стоит "0" — это индекс камеры/OBS Virtual Camera, обычно ничего менять не нужно</span>
            <span>• OBS: Инструменты → Запустить виртуальную камеру, и сразу жми "Подключить" — поле "0" уже готово</span>
            <span>• Вторая физическая камера/OBS — попробуй "1", если "0" занят</span>
            <span>• RTSP-камера: rtsp://логин:пароль@ip-адрес:554/поток</span>
            <span className="text-error/80">
              • Важно: если backend запущен в Docker, он видит камеру, только если она
              прокинута в контейнер (см. docker-compose.yml). Для локальной камеры/OBS
              надёжнее запускать backend через ./start-dev.sh (напрямую на хосте).
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
