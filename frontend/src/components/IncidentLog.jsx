import { EVENT_LABELS, SERVICE_LABELS, STATUS_STYLES, SEVERITY_STYLES } from "../mock/mockData";

export default function IncidentLog({ incidents }) {
  return (
    <div className="h-[180px] flex-shrink-0 glass-panel rounded-xl overflow-hidden flex flex-col border border-outline-variant/30 shadow-md">
      <div className="px-4 py-2 bg-surface/80 border-b border-outline-variant/30 flex justify-between items-center">
        <h3 className="font-headline-sm text-[14px] text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-primary-fixed">list_alt</span>
          Incident Log
        </h3>
        <div className="flex gap-2">
          <button className="text-on-surface-variant hover:text-on-surface transition-colors p-1">
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
          </button>
          <button className="text-on-surface-variant hover:text-on-surface transition-colors p-1">
            <span className="material-symbols-outlined text-[18px]">download</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto hide-scrollbar">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-surface-container-high/90 backdrop-blur font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant/20 z-10">
            <tr>
              <th className="py-2 px-4 font-normal">ID</th>
              <th className="py-2 px-4 font-normal">TIME</th>
              <th className="py-2 px-4 font-normal">EVENT</th>
              <th className="py-2 px-4 font-normal">SOURCE</th>
              <th className="py-2 px-4 font-normal">SEVERITY</th>
              <th className="py-2 px-4 font-normal">STATUS</th>
              <th className="py-2 px-4 font-normal">SERVICE</th>
              <th className="py-2 px-4 font-normal text-right">CONF.</th>
            </tr>
          </thead>
          <tbody className="font-data-mono text-[12px] text-on-surface divide-y divide-outline-variant/10">
            {incidents.map((incident) => (
              <tr
                key={incident.id}
                className={"table-row-hover cursor-default transition-colors " + (incident.status === "RESOLVED" ? "opacity-60" : "")}
              >
                <td className="py-2 px-4 text-primary-fixed">{incident.id}</td>
                <td className="py-2 px-4 text-outline">{incident.created_at}</td>
                <td className="py-2 px-4">{EVENT_LABELS[incident.event_type]}</td>
                <td className="py-2 px-4 text-on-surface-variant">{incident.source_name}</td>
                <td className="py-2 px-4">
                  <span className={"font-bold " + SEVERITY_STYLES[incident.severity]}>{incident.severity}</span>
                </td>
                <td className="py-2 px-4">
                  <span className={"px-2 py-0.5 rounded text-[10px] " + STATUS_STYLES[incident.status]}>
                    {incident.status}
                  </span>
                </td>
                <td className="py-2 px-4">{SERVICE_LABELS[incident.service]}</td>
                <td className="py-2 px-4 text-right">
                  {incident.confidence != null ? `${Math.round(incident.confidence * 100)}%` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
