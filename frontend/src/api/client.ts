import type {
  Alert,
  AlertListResponse,
  AlertSeverity,
  AlertStatus,
  Greenhouse,
  GreenhouseOverview,
  GreenhouseTopology,
  HistoryResponse,
  LatestReadingsResponse,
  Recommendation,
  RecommendationListResponse,
  RecommendationPriority,
  RecommendationStatus,
  Sensor,
  SensorType,
  TokenPair,
  User,
  UserRole,
  Zone,
  ZoneOverview,
} from "./types";

const BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8002";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Token storage (in-memory access + localStorage refresh)
// ---------------------------------------------------------------------------

const REFRESH_KEY = "gh_refresh_token";
let accessToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export const tokenStore = {
  getAccess(): string | null {
    return accessToken;
  },
  setAccess(token: string | null) {
    accessToken = token;
  },
  getRefresh(): string | null {
    try {
      return localStorage.getItem(REFRESH_KEY);
    } catch {
      return null;
    }
  },
  setRefresh(token: string | null) {
    try {
      if (token) localStorage.setItem(REFRESH_KEY, token);
      else localStorage.removeItem(REFRESH_KEY);
    } catch {
      /* localStorage unavailable (private mode) */
    }
  },
  clear() {
    accessToken = null;
    try {
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      /* ignore */
    }
  },
  onUnauthorized(cb: (() => void) | null) {
    onUnauthorized = cb;
  },
};

// ---------------------------------------------------------------------------
// Fetch with auth + refresh
// ---------------------------------------------------------------------------

let refreshPromise: Promise<TokenPair | null> | null = null;

async function performRefresh(): Promise<TokenPair | null> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return null;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return null;
    const pair = (await res.json()) as TokenPair;
    tokenStore.setAccess(pair.access_token);
    tokenStore.setRefresh(pair.refresh_token);
    return pair;
  } catch {
    return null;
  }
}

async function rawFetch<T>(
  path: string,
  init: RequestInit = {},
  allowRefresh: boolean = true
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  const access = tokenStore.getAccess();
  if (access) headers.Authorization = `Bearer ${access}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (res.status === 401 && allowRefresh && tokenStore.getRefresh()) {
    // Coalesce concurrent refreshes
    refreshPromise = refreshPromise ?? performRefresh();
    const pair = await refreshPromise;
    refreshPromise = null;
    if (pair) {
      return rawFetch<T>(path, init, false);
    }
    tokenStore.clear();
    onUnauthorized?.();
  }

  if (res.status === 401) {
    tokenStore.clear();
    onUnauthorized?.();
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || res.statusText);
  }
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  return (await res.json()) as T;
}

function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  return rawFetch<T>(path, init);
}

// ---------------------------------------------------------------------------
// Params
// ---------------------------------------------------------------------------

export interface HistoryParams {
  start_time?: string;
  end_time?: string;
  sensor_type?: SensorType;
  limit?: number;
  offset?: number;
}

export interface AlertFilters {
  greenhouse_id?: number;
  severity?: AlertSeverity;
  status?: AlertStatus;
  limit?: number;
  offset?: number;
}

export interface RecommendationFilters {
  greenhouse_id?: number;
  zone_id?: number;
  priority?: RecommendationPriority;
  status?: RecommendationStatus;
  limit?: number;
  offset?: number;
}

function qs(params: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  }
  return parts.length ? `?${parts.join("&")}` : "";
}

export const api = {
  // --- Auth ---
  login: (email: string, password: string) =>
    apiFetch<TokenPair>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  logout: (refresh_token: string) =>
    apiFetch<void>("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    }),
  me: () => apiFetch<User>("/auth/me"),
  listUsers: () => apiFetch<User[]>("/auth/users"),
  createUser: (payload: {
    email: string;
    full_name: string;
    password: string;
    role: UserRole;
  }) =>
    apiFetch<User>("/auth/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  // --- Core ---
  listGreenhouses: () => apiFetch<Greenhouse[]>("/greenhouses"),
  getGreenhouse: (id: number) => apiFetch<Greenhouse>(`/greenhouses/${id}`),
  listZones: (greenhouseId: number) =>
    apiFetch<Zone[]>(`/greenhouses/${greenhouseId}/zones`),
  listSensors: (zoneId: number) => apiFetch<Sensor[]>(`/zones/${zoneId}/sensors`),
  getTopology: () => apiFetch<GreenhouseTopology[]>("/topology"),

  // --- Analytics ---
  greenhouseOverview: (id: number, params: HistoryParams = {}) =>
    apiFetch<GreenhouseOverview>(`/greenhouses/${id}/overview${qs({ ...params })}`),
  zoneOverview: (id: number, params: HistoryParams = {}) =>
    apiFetch<ZoneOverview>(`/zones/${id}/overview${qs({ ...params })}`),
  latestReadings: (greenhouseId: number) =>
    apiFetch<LatestReadingsResponse>(`/greenhouses/${greenhouseId}/latest-readings`),
  greenhouseHistory: (id: number, params: HistoryParams = {}) =>
    apiFetch<HistoryResponse>(`/greenhouses/${id}/history${qs({ ...params })}`),
  sensorHistory: (id: number, params: HistoryParams = {}) =>
    apiFetch<HistoryResponse>(`/sensors/${id}/history${qs({ ...params })}`),

  // --- Alerts ---
  listAlerts: (filters: AlertFilters = {}) =>
    apiFetch<AlertListResponse>(`/alerts${qs({ ...filters })}`),
  greenhouseAlerts: (greenhouseId: number, filters: AlertFilters = {}) =>
    apiFetch<AlertListResponse>(
      `/greenhouses/${greenhouseId}/alerts${qs({ ...filters })}`
    ),
  acknowledgeAlert: (alertId: number) =>
    apiFetch<Alert>(`/alerts/${alertId}/acknowledge`, { method: "POST" }),
  resolveAlert: (alertId: number) =>
    apiFetch<Alert>(`/alerts/${alertId}/resolve`, { method: "POST" }),

  // --- Recommendations ---
  listRecommendations: (filters: RecommendationFilters = {}) =>
    apiFetch<RecommendationListResponse>(`/recommendations${qs({ ...filters })}`),
  greenhouseRecommendations: (
    greenhouseId: number,
    filters: RecommendationFilters = {}
  ) =>
    apiFetch<RecommendationListResponse>(
      `/greenhouses/${greenhouseId}/recommendations${qs({ ...filters })}`
    ),
  dismissRecommendation: (id: number) =>
    apiFetch<Recommendation>(`/recommendations/${id}/dismiss`, { method: "POST" }),
  completeRecommendation: (id: number) =>
    apiFetch<Recommendation>(`/recommendations/${id}/complete`, { method: "POST" }),
};