

export default function LiveCameraPanel({ source, detection, liveDetections = [], snapshotUrl }) {
  const isTracking = detection || liveDetections.length > 0;
  return (
    <div className="h-2/5 glass-panel rounded-xl overflow-hidden relative group">
      <div
        className="absolute inset-0 bg-cover bg-center bg-surface-container-high"
        style={snapshotUrl ? { backgroundImage: `url('${snapshotUrl}')` } : undefined}
      />

      {/* Тактическая сетка поверх картинки */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundSize: "40px 40px",
          backgroundImage:
            "linear-gradient(to right, #00f0ff 1px, transparent 1px), linear-gradient(to bottom, #00f0ff 1px, transparent 1px)",
        }}
      />

      <div className="absolute top-4 left-4 flex gap-3 items-start">
        <div className="bg-error text-on-error font-label-caps text-label-caps px-2 py-1 rounded shadow-lg flex items-center gap-1 pulse-critical">
          <div className="w-1.5 h-1.5 rounded-full bg-on-error" />
          LIVE
        </div>
        <div className="glass-panel px-3 py-1 rounded text-on-surface font-data-mono text-data-mono flex flex-col">
          <span>
            {source?.name ?? "NO SOURCE"} // {source?.location_label ?? "—"}
          </span>
          <span className="text-[10px] text-primary-fixed">
            {isTracking ? "TRACKING: AUTO-ENGAGED" : "TRACKING: IDLE"}
          </span>
        </div>
      </div>

      <div className="absolute bottom-4 right-4 glass-panel px-3 py-2 rounded text-primary-fixed font-data-mono text-[10px] text-right flex flex-col gap-1">
        <span>FOV: 85° | ZM: 2.1x</span>
        <span>
          LAT: {source?.lat?.toFixed(4) ?? "—"} | LON: {source?.lon?.toFixed(4) ?? "—"}
        </span>
        <span>FPS: 59.94 | BWT: 8.2Mbps</span>
      </div>

      {/* Реальные рамки уже нарисованы backend'ом на самом кадре (snapshotUrl).
          Здесь — только текстовая сводка того, что сейчас видит ИИ. */}
      {(detection || liveDetections.length > 0) && (
        <div className="absolute bottom-4 left-4 flex flex-col gap-1 items-start">
          {detection && (
            <div className="bg-error text-on-error font-data-mono text-[9px] px-2 py-1 rounded shadow-lg pulse-critical">
              {detection.label} CONF: {Math.round(detection.confidence * 100)}%
            </div>
          )}
          {liveDetections.map((d, i) => (
            <div
              key={`${d.class}-${i}`}
              className="glass-panel text-primary-fixed font-data-mono text-[9px] px-2 py-1 rounded"
            >
              {d.class.toUpperCase()} · {Math.round(d.confidence * 100)}%
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
