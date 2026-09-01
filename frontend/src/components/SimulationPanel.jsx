const SCENARIOS = [
  { key: "car_accident", label: "ДТП", emoji: "🚗", theme: "error" },
  { key: "fire", label: "ПОЖАР", emoji: "🔥", theme: "tertiary-container" },
  { key: "fall", label: "ПАДЕНИЕ", emoji: "🧍", theme: "tertiary-fixed" },
  { key: "pothole", label: "ЯМА", emoji: "🕳", theme: "outline" },
];

// theme -> набор классов Tailwind. Явные строки (не динамическая интерполяция),
// чтобы Tailwind JIT не срезал классы при сборке.
const THEME_CLASSES = {
  error: "bg-error/10 hover:bg-error/20 border-error/50 text-error",
  "tertiary-container":
    "bg-tertiary-container/10 hover:bg-tertiary-container/20 border-tertiary-container/50 text-tertiary-container",
  "tertiary-fixed":
    "bg-tertiary-fixed/10 hover:bg-tertiary-fixed/20 border-tertiary-fixed/50 text-tertiary-fixed",
  outline: "bg-outline/10 hover:bg-outline/20 border-outline/50 text-outline",
};

const ICON_BG_CLASSES = {
  error: "bg-error/20",
  "tertiary-container": "bg-tertiary-container/20",
  "tertiary-fixed": "bg-tertiary-fixed/20",
  outline: "bg-outline/20",
};

export default function SimulationPanel({ onRunScenario, runningScenario }) {
  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col gap-3 mt-auto">
      <h3 className="font-headline-sm text-headline-sm text-on-surface border-b border-outline-variant/30 pb-2 mb-1 flex items-center gap-2">
        <span className="material-symbols-outlined text-[18px] text-tertiary-fixed">science</span>
        Simulation Mode
      </h3>
      <div className="grid grid-cols-1 gap-2">
        {SCENARIOS.map((s) => {
          const isRunning = runningScenario === s.key;
          return (
            <button
              key={s.key}
              onClick={() => onRunScenario(s.key)}
              disabled={isRunning}
              className={
                "rounded-lg py-2 px-3 flex items-center gap-3 transition-all group border " +
                THEME_CLASSES[s.theme] +
                (isRunning ? " opacity-50 cursor-wait" : "")
              }
            >
              <div
                className={
                  "w-6 h-6 rounded flex items-center justify-center group-hover:scale-110 transition-transform " +
                  ICON_BG_CLASSES[s.theme] +
                  (s.key === "pothole" ? " filter grayscale" : "")
                }
              >
                {s.emoji}
              </div>
              <span className="font-label-caps text-label-caps font-bold">
                {isRunning ? "ЗАПУСК..." : s.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
