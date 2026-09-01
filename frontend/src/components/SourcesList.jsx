export default function SourcesList({ sources, selectedSourceId, onSelect }) {
  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col gap-3">
      <h3 className="font-headline-sm text-headline-sm text-on-surface border-b border-outline-variant/30 pb-2 mb-1 flex justify-between items-center">
        Active Sources
        <span className="font-data-mono text-[10px] text-primary-fixed bg-primary-fixed/10 px-2 py-0.5 rounded-full">
          LIVE
        </span>
      </h3>
      <div className="flex flex-col gap-2">
        {sources.map((source) => {
          const isActive = source.status === "active";
          const isSelected = source.id === selectedSourceId;
          return (
            <div
              key={source.id}
              onClick={() => isActive && onSelect(source.id)}
              className={
                "flex items-center gap-3 p-2 rounded-lg border transition-colors group " +
                (isActive
                  ? "bg-surface-container border-outline-variant/20 hover:border-primary-fixed/50 cursor-pointer"
                  : "bg-surface-container/50 border-outline-variant/10 opacity-60") +
                (isSelected ? " border-primary-fixed/70" : "")
              }
            >
              <div className="w-8 h-8 rounded bg-surface border border-outline-variant/50 overflow-hidden relative flex items-center justify-center">
                {source.thumbnail ? (
                  <div
                    className="w-full h-full bg-cover bg-center"
                    style={{ backgroundImage: `url('${source.thumbnail}')` }}
                  />
                ) : (
                  <span className="material-symbols-outlined text-outline text-[16px]">videocam_off</span>
                )}
              </div>
              <div className="flex-1 flex flex-col min-w-0">
                <span
                  className={
                    "font-label-caps text-label-caps truncate " +
                    (isActive ? "text-on-surface" : "text-outline")
                  }
                >
                  {source.name}
                </span>
                <span
                  className={"font-data-mono text-[9px] truncate " + (isActive ? "text-on-surface-variant" : "text-outline")}
                >
                  {source.location_label}
                </span>
              </div>
              <div
                className={
                  "w-2 h-2 rounded-full flex-shrink-0 " +
                  (isActive ? "bg-primary-fixed shadow-[0_0_8px_rgba(125,244,255,0.6)]" : "bg-outline")
                }
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
