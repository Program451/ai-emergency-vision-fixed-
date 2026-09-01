import IncidentCard from "./IncidentCard.jsx";

export default function IncidentPanel({ incidents, onAssignOperator }) {
  const activeCount = incidents.filter((i) => i.status !== "RESOLVED").length;

  return (
    <div className="w-[320px] flex-shrink-0 flex flex-col bg-surface-container/60 backdrop-blur-md rounded-xl border border-outline-variant/30 overflow-hidden shadow-lg relative">
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-error/50 to-transparent" />

      <div className="p-4 border-b border-outline-variant/30 flex justify-between items-center bg-surface/50">
        <h2 className="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px] text-error">warning</span>
          Active Incidents
        </h2>
        <span className="bg-error/20 text-error font-data-mono text-data-mono px-2 py-0.5 rounded-full border border-error/30">
          {activeCount}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3 hide-scrollbar">
        {incidents.length === 0 ? (
          <div className="text-body-sm text-on-surface-variant text-center py-8">
            Нет активных происшествий. Запустите сценарий в Simulation Mode.
          </div>
        ) : (
          incidents.map((incident) => (
            <IncidentCard key={incident.id} incident={incident} onAssignOperator={onAssignOperator} />
          ))
        )}
      </div>
    </div>
  );
}
