import { useEffect, useState } from "react";

export default function TopBar({ activeSourcesCount, totalSourcesCount }) {
  const [clock, setClock] = useState(formatClock());

  useEffect(() => {
    const id = setInterval(() => setClock(formatClock()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="fixed top-0 w-full z-50 flex justify-between items-center px-container-padding h-16 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/20 shadow-sm">
      <div className="flex items-center gap-6">
        <div className="font-headline-md text-headline-md font-bold tracking-tight text-primary-container">
          EOC COMMAND INTERFACE
        </div>

        <div className="relative hidden lg:block w-64">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">
            search
          </span>
          <input
            className="w-full bg-surface-container-high/50 border border-outline-variant/50 rounded-full py-1.5 pl-9 pr-4 text-body-sm text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
            placeholder="Search resources..."
            type="text"
          />
        </div>

        <div className="flex flex-col ml-4">
          <span className="font-label-caps text-label-caps text-on-surface-variant">System</span>
          <span className="font-data-mono text-data-mono text-primary-fixed">AI Emergency Vision</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4 border-r border-outline-variant/30 pr-6 mr-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary-fixed" />
            <span className="font-data-mono text-data-mono text-primary-fixed">
              {activeSourcesCount}/{totalSourcesCount} sources active
            </span>
          </div>
          <div className="font-data-mono text-data-mono text-on-surface-variant ml-4">{clock}</div>
        </div>

        <button className="bg-primary-container text-on-primary-container hover:bg-surface-bright/10 transition-colors cursor-pointer active:scale-95 px-4 py-1.5 rounded-lg font-label-caps text-label-caps flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">cell_tower</span>
          GO LIVE
        </button>

        <div className="flex items-center gap-3">
          <button className="text-on-surface-variant hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="text-on-surface-variant hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <button className="text-on-surface-variant hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined">help</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-surface-container-highest overflow-hidden border border-outline-variant flex items-center justify-center ml-2">
            <span className="material-symbols-outlined text-on-surface-variant text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function formatClock() {
  const now = new Date();
  return now.toISOString().replace("T", " ").substring(0, 19) + " UTC";
}
