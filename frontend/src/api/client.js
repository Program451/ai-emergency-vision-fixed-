

const BASE_URL = "/api";

export async function fetchSources() {
  const res = await fetch(`${BASE_URL}/sources`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  return res.json();
}

export async function fetchIncidents(statusFilter) {
  const url = statusFilter
    ? `${BASE_URL}/incidents?status=${statusFilter}`
    : `${BASE_URL}/incidents`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch incidents");
  return res.json();
}

export async function updateIncidentStatus(incidentId, status) {
  const res = await fetch(`${BASE_URL}/incidents/${incidentId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Failed to update incident status");
  return res.json();
}

export async function createSource({ name, type, stream_url, lat, lon, location_label }) {
  const res = await fetch(`${BASE_URL}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, type, stream_url, lat, lon, location_label }),
  });
  if (!res.ok) throw new Error("Failed to create source");
  return res.json();
}

// Загрузка демо-видео с прогрессом. Используем XHR вместо fetch,
// потому что fetch не даёт onUploadProgress — а для демо это важно
// показать красиво (прогресс-бар), а не просто "спиннер в никуда".
export function uploadDemoVideo(file, { name, onProgress } = {}) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);
    if (name) formData.append("name", name);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE_URL}/uploads/video`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (err) {
          reject(new Error("Bad response from server"));
        }
      } else {
        let message = "Ошибка загрузки видео";
        try {
          message = JSON.parse(xhr.responseText).detail || message;
        } catch {
          /* ignore */
        }
        reject(new Error(message));
      }
    };

    xhr.onerror = () => reject(new Error("Сеть недоступна"));
    xhr.send(formData);
  });
}

// Загрузка одной фотографии — ИИ анализирует один кадр и сразу возвращает
// картинку с нарисованными рамками найденных проблем (см. /uploads/photo).
export function uploadDemoPhoto(file, { lat, lon, onProgress } = {}) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);
    if (lat != null) formData.append("lat", lat);
    if (lon != null) formData.append("lon", lon);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE_URL}/uploads/photo`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (err) {
          reject(new Error("Bad response from server"));
        }
      } else {
        let message = "Ошибка загрузки фото";
        try {
          message = JSON.parse(xhr.responseText).detail || message;
        } catch {
          /* ignore */
        }
        reject(new Error(message));
      }
    };

    xhr.onerror = () => reject(new Error("Сеть недоступна"));
    xhr.send(formData);
  });
}

export async function startSource(sourceId) {
  const res = await fetch(`${BASE_URL}/sources/${sourceId}/start`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start source");
  return res.json();
}

export async function stopSource(sourceId) {
  const res = await fetch(`${BASE_URL}/sources/${sourceId}/stop`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to stop source");
  return res.json();
}

export async function runSimulation(scenario) {
  const res = await fetch(`${BASE_URL}/simulate/${scenario}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start simulation");
  return res.json();
}

// WebSocket-подключение для realtime-обновлений incidents.
// onIncident вызывается на каждый новый/изменённый incident.
export function connectIncidentSocket(onIncident) {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${proto}://${window.location.host}/ws/incidents`);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onIncident(data);
    } catch (err) {
      console.error("Bad WS payload", err);
    }
  };

  socket.onerror = (err) => console.error("Incident socket error", err);

  return () => socket.close();
}
