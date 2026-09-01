// Моковые данные для разработки Dashboard, пока backend Event API не готов.
// Формат полей ЗЕРКАЛИТ backend/app/config.py (VALID_EVENT_TYPES, VALID_SEVERITIES,
// VALID_STATUSES, VALID_SERVICES) — когда подключим реальный API, менять структуру
// компонентов не придётся, только источник данных (см. src/api/client.js).

export const EVENT_LABELS = {
  car_accident: "ДТП",
  fire: "ПОЖАР",
  smoke: "ДЫМ",
  person_fallen: "ПАДЕНИЕ",
  pothole: "ЯМА",
};

export const SERVICE_LABELS = {
  EMERGENCY_MEDICAL: "🚑 EMERGENCY MEDICAL",
  FIRE_DEPARTMENT: "🚒 FIRE DEPT",
  POLICE: "🚓 POLICE",
  ROAD_MAINTENANCE: "🚧 CITY MAINTENANCE",
};

export const STATUS_STYLES = {
  NEW: "bg-error text-on-error",
  CONFIRMED: "bg-tertiary-container text-on-tertiary-container",
  SENT: "bg-secondary-container text-on-secondary-container",
  RESOLVED: "bg-surface-variant text-on-surface-variant border border-outline-variant",
};

export const SEVERITY_STYLES = {
  CRITICAL: "text-error",
  HIGH: "text-tertiary-container",
  MEDIUM: "text-tertiary-fixed",
  LOW: "text-outline",
};

export const mockSources = [
  {
    id: 1,
    name: "CAM-SEC-01",
    type: "camera",
    location_label: "Main St / 5th Ave",
    status: "active",
    thumbnail:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAd5QyA6g3aJL22g9DIsbLXEJTpErGLzNy1fobnhta-hutQaqMXJXcH_e-Jb7Bqd8_KWl3FyKToAo1sgbclqMQLtWGLhkHhxtfjxoi5ZjHD-8NIsTPipl-E6nDtZC8bIcBuufdMYymyi5f07xs8zrlF-08RFw1ojbdKcd6tueTpGN1fk7a1mJdnwDfbCjJ_RrgcuoEziBGU-r1y6Vqp--14EnuzQJ7AGWYqHFRenK2JwwrFUhxlYKxa",
  },
  {
    id: 2,
    name: "DRONE-A7",
    type: "drone",
    location_label: "Sector G, Patrol",
    status: "active",
    thumbnail:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBcDXEYvo0_c1yDqRMAhdASpkC362kk014W3Jf4q-5Pf1EBAphPKQlKt_ajZimjC-xHA7u6jgCQ8ScUD-_E1Hqjtks_FP2qaRL4rRiL2ndjWyzLt3_RaukFBm3UlWzJXIpPag6A7OoAKbwo8ON2HGiFR_Ay_t5DRYfinwf7x6I1MVOSxL3jdV1-57QVaEvCufbrEHPf6byQJRZDBrVqSaDyOGPgz94bnE5Crdgk6qA2gTFiTD0RLmQY",
  },
  {
    id: 3,
    name: "CAM-IND-12",
    type: "camera",
    location_label: "Maintenance",
    status: "inactive",
    thumbnail: null,
  },
];

export const mockIncidents = [
  {
    id: "INC-9942",
    event_type: "car_accident",
    confidence: 0.98,
    severity: "CRITICAL",
    service: "EMERGENCY_MEDICAL",
    reason: "Multiple vehicle collision detected. Immediate response recommended.",
    lat: 55.7558,
    lon: 37.6173,
    source_name: "CAM-SEC-01",
    status: "NEW",
    created_at: "14:31:42",
  },
  {
    id: "INC-9941",
    event_type: "fire",
    confidence: 0.85,
    severity: "HIGH",
    service: "FIRE_DEPARTMENT",
    reason: "Smoke signature detected near storage facility B.",
    lat: null,
    lon: null,
    location_label: "Sector 4, Industrial Zone",
    source_name: "DRONE-A7",
    status: "SENT",
    created_at: "14:15:20",
  },
  {
    id: "INC-9940",
    event_type: "person_fallen",
    confidence: 0.92,
    severity: "MEDIUM",
    service: "EMERGENCY_MEDICAL",
    reason: null,
    location_label: "Main St / 2nd Ave",
    source_name: "CAM-PUB-04",
    status: "RESOLVED",
    created_at: "13:45:01",
  },
  {
    id: "INC-9939",
    event_type: "pothole",
    confidence: 0.78,
    severity: "LOW",
    service: "ROAD_MAINTENANCE",
    reason: null,
    location_label: "Main St / 2nd Ave",
    source_name: "DASHCAM-M1",
    status: "RESOLVED",
    created_at: "10:05:00",
  },
];

export const mockMapMarkers = [
  { id: "INC-9938", severity: "LOW", top: "25%", left: "25%" },
  { id: "INC-9937", severity: "MEDIUM", top: "66%", left: "33%" },
  {
    id: "INC-9942",
    severity: "CRITICAL",
    top: "50%",
    left: "50%",
    popup: mockIncidents[0],
  },
];
