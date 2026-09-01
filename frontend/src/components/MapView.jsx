import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { EVENT_LABELS, SERVICE_LABELS } from "../mock/mockData";

const SEVERITY_COLOR = {
  CRITICAL: "#ffb4ab", // error
  HIGH: "#fed639", // tertiary-container
  MEDIUM: "#ffe179", // tertiary-fixed
  LOW: "#849495", // outline
};

function markerIcon(severity) {
  const color = SEVERITY_COLOR[severity] ?? SEVERITY_COLOR.LOW;
  const pulse = severity === "CRITICAL" ? "pulse-critical" : "";
  return L.divIcon({
    className: "",
    html: `<div class="${pulse}" style="
        width:16px;height:16px;border-radius:9999px;
        background:${color};
        border:2px solid #051424;
        box-shadow:0 0 10px ${color}CC;
      "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

const DEFAULT_CENTER = [42.9, 71.3667]; // Тараз — совпадает с demo-координатами Simulation Mode

export default function MapView({ incidents, onRequestOperator }) {
  const withCoords = incidents.filter((i) => i.lat != null && i.lon != null);

  return (
    <div className="h-3/5 glass-panel rounded-xl overflow-hidden relative">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={13}
        scrollWheelZoom
        style={{ height: "100%", width: "100%", background: "#051424" }}
      >
        {/* Тёмная тема тайлов CARTO — бесплатная, без API-ключа */}
        <TileLayer
          attribution='&copy; OpenStreetMap contributors &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {withCoords.map((incident) => (
          <Marker key={incident.id} position={[incident.lat, incident.lon]} icon={markerIcon(incident.severity)}>
            <Popup>
              <div className="font-data-mono text-[11px] text-on-surface flex flex-col gap-1 min-w-[180px]">
                <div className="flex justify-between items-center border-b border-outline-variant/30 pb-1 mb-1">
                  <span className="font-bold" style={{ color: SEVERITY_COLOR[incident.severity] }}>
                    {EVENT_LABELS[incident.event_type]} Обнаружено
                  </span>
                  <span className="font-bold">{Math.round(incident.confidence * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>LOC:</span>
                  <span>
                    {incident.lat.toFixed(4)}, {incident.lon.toFixed(4)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>SRC:</span>
                  <span>{incident.source_name}</span>
                </div>
                <button
                  onClick={() => onRequestOperator?.(incident.id)}
                  className="mt-2 w-full border rounded py-1 text-[10px] font-bold"
                  style={{ borderColor: SEVERITY_COLOR[incident.severity], color: SEVERITY_COLOR[incident.severity] }}
                >
                  REQ: {SERVICE_LABELS[incident.service]}
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
