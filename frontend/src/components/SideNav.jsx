const TABS = [
  { icon: "videocam", label: "Live Feeds", active: true },
  { icon: "videocam_off", label: "Drones", active: false },
  { icon: "precision_manufacturing", label: "Simulations", active: false },
  { icon: "insights", label: "Telemetry", active: false },
  { icon: "history", label: "Archives", active: false },
];

export default function SideNav() {
  return (
    <nav className="fixed left-0 top-16 h-[calc(100vh-64px)] flex flex-col z-40 bg-surface-container-low/90 backdrop-blur-md border-r border-outline-variant/10 w-60">
      <div className="p-4 border-b border-outline-variant/10 mb-2">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant/30 flex items-center justify-center overflow-hidden">
            <span className="material-symbols-outlined text-primary-fixed">admin_panel_settings</span>
          </div>
          <div>
            <h2 className="font-headline-sm text-headline-sm text-on-surface">OPERATIONS</h2>
            <p className="font-label-caps text-label-caps text-on-surface-variant">Vigilance Alpha-9</p>
          </div>
        </div>
        <button className="w-full py-2 bg-surface-container border border-outline-variant/30 rounded-lg text-primary-container font-label-caps text-label-caps hover:bg-surface-container-high transition-all duration-200 ease-in-out flex justify-center items-center gap-2">
          <span className="material-symbols-outlined text-[16px]">add</span>
          NEW SIMULATION
        </button>
      </div>

      <div className="flex-1 flex flex-col gap-1 px-2 py-2">
        {TABS.map((tab) => (
          <button
            key={tab.label}
            className={
              "flex items-center gap-3 px-3 py-2 rounded-lg mx-2 cursor-pointer active:scale-95 duration-200 ease-in-out font-label-caps text-label-caps transition-all " +
              (tab.active
                ? "bg-secondary-container text-on-secondary-container"
                : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high")
            }
          >
            <span
              className="material-symbols-outlined text-[20px]"
              style={tab.active ? { fontVariationSettings: "'FILL' 1" } : undefined}
            >
              {tab.icon}
            </span>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-2 border-t border-outline-variant/10">
        <button className="flex items-center gap-3 w-full px-3 py-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-all rounded-lg mx-2 cursor-pointer duration-200 ease-in-out font-label-caps text-label-caps">
          <span className="material-symbols-outlined text-[20px]">settings</span>
          Settings
        </button>
        <button className="flex items-center gap-3 w-full px-3 py-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-all rounded-lg mx-2 cursor-pointer duration-200 ease-in-out font-label-caps text-label-caps">
          <span className="material-symbols-outlined text-[20px]">logout</span>
          Logout
        </button>
      </div>
    </nav>
  );
}
