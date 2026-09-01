import { EVENT_LABELS, SERVICE_LABELS, STATUS_STYLES, SEVERITY_STYLES } from "../mock/mockData";

const EVENT_ICON = {
  car_accident: "directions_car",
  fire: "local_fire_department",
  smoke: "local_fire_department",
  person_fallen: "personal_injury",
  pothole: "warning",
};

const BORDER_COLOR = {
  CRITICAL: "border-l-error",
  HIGH: "border-l-tertiary-container",
  MEDIUM: "border-l-tertiary-fixed",
  LOW: "border-l-outline",
};

const BAR_COLOR = {
  CRITICAL: "bg-error",
  HIGH: "bg-tertiary-container",
  MEDIUM: "bg-tertiary-fixed",
  LOW: "bg-outline",
};

export default function IncidentCard({ incident, onAssignOperator }) {
  const isResolved = incident.status === "RESOLVED";
  const isSent = incident.status === "SENT";
  const isActionable = !isResolved && !isSent;

  return (
    <div
      className={
        "bg-surface-container-high rounded-lg p-3 border-l-4 border border-outline-variant/20 shadow-sm relative overflow-hidden " +
        BORDER_COLOR[incident.severity] +
        (isResolved ? " opacity-80" : "")
      }
    >
      <div className="absolute top-0 right-0 p-2 opacity-10 pointer-events-none">
        <span className="material-symbols-outlined text-[64px]" style={{ color: "currentColor" }}>
          {EVENT_ICON[incident.event_type] ?? "warning"}
        </span>
      </div>

      <div className="flex justify-between items-start mb-2 relative z-10">
        <div className="flex items-center gap-2">
          <span className={"font-label-caps text-[10px] px-1.5 py-0.5 rounded " + STATUS_STYLES[incident.status]}>
            {incident.status}
          </span>
          <span className="font-headline-sm text-[14px] text-on-surface font-bold">
            {EVENT_LABELS[incident.event_type]}
          </span>
        </div>
        <span className="font-data-mono text-[10px] text-on-surface-variant">{incident.created_at}</span>
      </div>

      {incident.confidence != null && (
        <div className="flex items-center gap-2 mb-2 relative z-10">
          <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden">
            <div
              className={"h-full " + BAR_COLOR[incident.severity]}
              style={{ width: `${Math.round(incident.confidence * 100)}%` }}
            />
          </div>
          <span className={"font-data-mono text-[10px] " + SEVERITY_STYLES[incident.severity]}>
            CONF: {Math.round(incident.confidence * 100)}%
          </span>
        </div>
      )}

      <div className="font-data-mono text-[11px] text-on-surface-variant mb-2 relative z-10">
        <span className="material-symbols-outlined text-[14px] align-middle mr-1">location_on</span>
        {incident.lat != null ? `${incident.lat.toFixed(4)} N, ${incident.lon.toFixed(4)} E` : incident.location_label}
      </div>

      {incident.reason && (
        <div className="text-body-sm text-outline mb-3 relative z-10 italic">"{incident.reason}"</div>
      )}

      {isActionable && (
        <button
          onClick={() => onAssignOperator(incident.id)}
          className="w-full bg-error text-on-error font-label-caps text-[11px] py-2 rounded shadow hover:bg-error/90 transition-colors flex justify-center items-center gap-2 relative z-10"
        >
          <span className="material-symbols-outlined text-[16px]">support_agent</span>
          Передать оператору
        </button>
      )}

      {isSent && (
        <button
          disabled
          className="w-full bg-surface border border-outline-variant/50 text-on-surface font-label-caps text-[11px] py-2 rounded flex justify-center items-center gap-2 relative z-10 opacity-70"
        >
          <span className="material-symbols-outlined text-[16px]">check_circle</span>
          DISPATCHED
        </button>
      )}

      <div className="mt-2 text-center relative z-10">
        <span className={"font-label-caps text-[9px] " + SEVERITY_STYLES[incident.severity]}>
          REC: {SERVICE_LABELS[incident.service]}
        </span>
      </div>
    </div>
  );
}
