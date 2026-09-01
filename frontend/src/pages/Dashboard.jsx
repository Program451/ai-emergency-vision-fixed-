import { useEffect, useMemo, useState, useCallback } from "react";
import TopBar from "../components/TopBar.jsx";
import SideNav from "../components/SideNav.jsx";
import SourcesList from "../components/SourcesList.jsx";
import SimulationPanel from "../components/SimulationPanel.jsx";
import UploadDemoPanel from "../components/UploadDemoPanel.jsx";
import LiveCameraPanel from "../components/LiveCameraPanel.jsx";
import MapView from "../components/MapView.jsx";
import IncidentPanel from "../components/IncidentPanel.jsx";
import IncidentLog from "../components/IncidentLog.jsx";
import {
  fetchSources,
  fetchIncidents,
  updateIncidentStatus,
  runSimulation,
  connectIncidentSocket,
} from "../api/client.js";
import { mockSources, mockIncidents } from "../mock/mockData";

export default function Dashboard() {
  const [sources, setSources] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [selectedSourceId, setSelectedSourceId] = useState(null);
  const [runningScenario, setRunningScenario] = useState(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [liveDetections, setLiveDetections] = useState({}); // { [source_id]: { detections, at } }

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [srcs, incs] = await Promise.all([fetchSources(), fetchIncidents()]);
        if (cancelled) return;
        setSources(mapSources(srcs));
        setIncidents(mapIncidents(srcs, incs));
        setBackendAvailable(true);
      } catch (err) {
        console.warn("Backend недоступен, использую mock-данные:", err.message);
        if (cancelled) return;
        setSources(mockSources);
        setIncidents(mockIncidents);
        setBackendAvailable(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (selectedSourceId == null && sources.length > 0) {
      setSelectedSourceId(sources[0].id);
    }
  }, [sources, selectedSourceId]);

  useEffect(() => {
    if (!backendAvailable) return;

    const disconnect = connectIncidentSocket((msg) => {
      if (msg.type === "incident_created") {
        setIncidents((prev) => [mapIncident(sources, msg.incident), ...prev]);
      } else if (msg.type === "incident_updated") {
        setIncidents((prev) =>
          prev.map((i) => (i.id === msg.incident.id ? { ...i, status: msg.incident.status } : i))
        );
      } else if (msg.type === "live_detection") {
        // Реальные детекты ИИ на текущем кадре (не обязательно подтверждённый incident) —
        // сами рамки уже "вшиты" backend'ом в снапшот, здесь только текстовый статус.
        setLiveDetections((prev) => ({
          ...prev,
          [msg.source_id]: { detections: msg.detections, at: Date.now() },
        }));
      }
    });

    return disconnect;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendAvailable, sources]);

  const activeSourcesCount = sources.filter((s) => s.status === "active").length;
  const selectedSource = useMemo(
    () => sources.find((s) => s.id === selectedSourceId) ?? null,
    [sources, selectedSourceId]
  );

  const activeDetection = useMemo(() => {
    const critical = incidents.find(
      (i) => i.status === "NEW" && i.severity === "CRITICAL" && i.source_name === selectedSource?.name
    );
    if (!critical) return null;
    return {
      label: critical.event_type === "car_accident" ? "ДТП" : critical.event_type,
      confidence: critical.confidence,
    };
  }, [incidents, selectedSource]);

  // Живые (ещё не обязательно подтверждённые) детекты для выбранного источника —
  // сама рамка уже нарисована backend'ом прямо на снапшоте, это только текст-статус.
  const currentLiveDetections = useMemo(() => {
    if (!selectedSource) return [];
    const entry = liveDetections[selectedSource.id];
    if (!entry) return [];
    if (Date.now() - entry.at > 4000) return []; // считаем "устаревшим", если давно не обновлялось
    return entry.detections;
  }, [liveDetections, selectedSource]);

  const handleAssignOperator = useCallback(
    async (incidentId) => {
      setIncidents((prev) => prev.map((i) => (i.id === incidentId ? { ...i, status: "SENT" } : i)));
      if (!backendAvailable) return;
      try {
        await updateIncidentStatus(incidentId, "SENT");
      } catch (err) {
        console.error("Не удалось обновить статус incident:", err);
      }
    },
    [backendAvailable]
  );

  const handleSourceReady = useCallback(
    async (source) => {
      // Новый source создан и (обычно) уже запущен backend'ом — подтягиваем
      // свежий список, чтобы он тут же появился в SourcesList, и выбираем его.
      if (!backendAvailable) return;
      try {
        const srcs = await fetchSources();
        setSources(mapSources(srcs));
        setSelectedSourceId(source.id);
      } catch (err) {
        console.error("Не удалось обновить список источников:", err);
      }
    },
    [backendAvailable]
  );

  const handleRunScenario = useCallback(
    async (scenarioKey) => {
      setRunningScenario(scenarioKey);
      if (!backendAvailable) {
        setTimeout(() => setRunningScenario(null), 1500);
        return;
      }
      try {
        await runSimulation(scenarioKey);
        const srcs = await fetchSources();
        setSources(mapSources(srcs));
      } catch (err) {
        console.error("Не удалось запустить симуляцию:", err);
      } finally {
        setRunningScenario(null);
      }
    },
    [backendAvailable]
  );

  return (
    <>
      <TopBar activeSourcesCount={activeSourcesCount} totalSourcesCount={sources.length} />
      <SideNav />

      <main className="ml-60 mt-16 p-gutter h-[calc(100vh-64px)] flex flex-col gap-gutter overflow-hidden relative">
        <div className="flex-1 flex gap-gutter min-h-0 overflow-hidden">
          <div className="w-[220px] flex-shrink-0 flex flex-col gap-gutter hide-scrollbar overflow-y-auto">
            <SourcesList sources={sources} selectedSourceId={selectedSourceId} onSelect={setSelectedSourceId} />
            <UploadDemoPanel onSourceReady={handleSourceReady} />
            <SimulationPanel onRunScenario={handleRunScenario} runningScenario={runningScenario} />
          </div>

          <div className="flex-1 flex flex-col gap-gutter min-w-0">
            <LiveCameraPanel
              source={selectedSource}
              detection={activeDetection}
              liveDetections={currentLiveDetections}
              snapshotUrl={
                selectedSource && backendAvailable
                  ? `/snapshots/${selectedSource.id}.jpg?t=${Math.floor(Date.now() / 1000)}`
                  : null
              }
            />
            <MapView incidents={incidents} onRequestOperator={handleAssignOperator} />
          </div>

          <IncidentPanel incidents={incidents} onAssignOperator={handleAssignOperator} />
        </div>

        <IncidentLog incidents={incidents} />
      </main>
    </>
  );
}

function mapSources(backendSources) {
  return backendSources.map((s) => ({
    id: s.id,
    name: s.name,
    type: s.type,
    location_label: s.location_label,
    status: s.status,
    thumbnail: null,
    lat: s.lat,
    lon: s.lon,
  }));
}

function mapIncidents(backendSources, backendIncidents) {
  return backendIncidents.map((inc) => mapIncident(backendSources, inc));
}

function mapIncident(sourcesList, inc) {
  const source = sourcesList.find((s) => s.id === inc.source_id);
  return {
    id: inc.id,
    event_type: inc.event_type,
    confidence: inc.confidence,
    severity: inc.severity,
    service: inc.service,
    reason: inc.reason,
    lat: inc.lat,
    lon: inc.lon,
    source_name: source?.name ?? `SRC-${inc.source_id}`,
    status: inc.status,
    created_at: new Date(inc.created_at).toLocaleTimeString("ru-RU"),
  };
}
