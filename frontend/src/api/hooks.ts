import { useQuery, useQueries } from "@tanstack/react-query";
import {
  api,
  type AlertFilters,
  type HistoryParams,
  type RecommendationFilters,
} from "./client";

export const queryKeys = {
  greenhouses: ["greenhouses"] as const,
  greenhouse: (id: number) => ["greenhouse", id] as const,
  zones: (ghId: number) => ["zones", ghId] as const,
  sensors: (zoneId: number) => ["sensors", zoneId] as const,
  topology: ["topology"] as const,
  greenhouseOverview: (id: number, params?: HistoryParams) =>
    ["greenhouse-overview", id, params ?? {}] as const,
  zoneOverview: (id: number, params?: HistoryParams) =>
    ["zone-overview", id, params ?? {}] as const,
  latestReadings: (id: number) => ["latest-readings", id] as const,
  greenhouseHistory: (id: number, params?: HistoryParams) =>
    ["greenhouse-history", id, params ?? {}] as const,
  sensorHistory: (id: number, params?: HistoryParams) =>
    ["sensor-history", id, params ?? {}] as const,
  alerts: (filters?: AlertFilters) => ["alerts", filters ?? {}] as const,
  greenhouseAlerts: (id: number, filters?: AlertFilters) =>
    ["greenhouse-alerts", id, filters ?? {}] as const,
  openAlertsCount: ["alerts", "open-count"] as const,
  recommendations: (filters?: RecommendationFilters) =>
    ["recommendations", filters ?? {}] as const,
  greenhouseRecommendations: (id: number, filters?: RecommendationFilters) =>
    ["greenhouse-recommendations", id, filters ?? {}] as const,
  openRecommendationsCount: ["recommendations", "open-count"] as const,
};

// --- Core ---

export const useGreenhouses = () =>
  useQuery({ queryKey: queryKeys.greenhouses, queryFn: api.listGreenhouses });

export const useGreenhouse = (id: number) =>
  useQuery({
    queryKey: queryKeys.greenhouse(id),
    queryFn: () => api.getGreenhouse(id),
    enabled: Number.isFinite(id) && id > 0,
  });

export const useZones = (greenhouseId: number) =>
  useQuery({
    queryKey: queryKeys.zones(greenhouseId),
    queryFn: () => api.listZones(greenhouseId),
    enabled: Number.isFinite(greenhouseId) && greenhouseId > 0,
  });

export const useSensors = (zoneId: number) =>
  useQuery({
    queryKey: queryKeys.sensors(zoneId),
    queryFn: () => api.listSensors(zoneId),
    enabled: Number.isFinite(zoneId) && zoneId > 0,
  });

export const useTopology = () =>
  useQuery({ queryKey: queryKeys.topology, queryFn: api.getTopology });

// --- Analytics ---

export const useGreenhouseOverview = (id: number, params: HistoryParams = {}) =>
  useQuery({
    queryKey: queryKeys.greenhouseOverview(id, params),
    queryFn: () => api.greenhouseOverview(id, params),
    enabled: Number.isFinite(id) && id > 0,
  });

export const useZoneOverview = (id: number, params: HistoryParams = {}) =>
  useQuery({
    queryKey: queryKeys.zoneOverview(id, params),
    queryFn: () => api.zoneOverview(id, params),
    enabled: Number.isFinite(id) && id > 0,
  });

export const useLatestReadings = (greenhouseId: number) =>
  useQuery({
    queryKey: queryKeys.latestReadings(greenhouseId),
    queryFn: () => api.latestReadings(greenhouseId),
    enabled: Number.isFinite(greenhouseId) && greenhouseId > 0,
  });

export const useGreenhouseHistory = (id: number, params: HistoryParams = {}) =>
  useQuery({
    queryKey: queryKeys.greenhouseHistory(id, params),
    queryFn: () => api.greenhouseHistory(id, params),
    enabled: Number.isFinite(id) && id > 0,
  });

export const useSensorHistory = (id: number, params: HistoryParams = {}) =>
  useQuery({
    queryKey: queryKeys.sensorHistory(id, params),
    queryFn: () => api.sensorHistory(id, params),
    enabled: Number.isFinite(id) && id > 0,
  });

// --- Alerts ---

export const useAlerts = (filters: AlertFilters = {}) =>
  useQuery({
    queryKey: queryKeys.alerts(filters),
    queryFn: () => api.listAlerts(filters),
  });

export const useGreenhouseAlerts = (id: number, filters: AlertFilters = {}) =>
  useQuery({
    queryKey: queryKeys.greenhouseAlerts(id, filters),
    queryFn: () => api.greenhouseAlerts(id, filters),
    enabled: Number.isFinite(id) && id > 0,
  });

export const useOpenAlertsCount = () =>
  useQuery({
    queryKey: queryKeys.openAlertsCount,
    queryFn: () => api.listAlerts({ status: "open", limit: 1 }),
    refetchInterval: 30_000,
    select: (data) => data.total,
  });

// --- Recommendations ---

export const useRecommendations = (filters: RecommendationFilters = {}) =>
  useQuery({
    queryKey: queryKeys.recommendations(filters),
    queryFn: () => api.listRecommendations(filters),
  });

export const useGreenhouseRecommendations = (
  id: number,
  filters: RecommendationFilters = {}
) =>
  useQuery({
    queryKey: queryKeys.greenhouseRecommendations(id, filters),
    queryFn: () => api.greenhouseRecommendations(id, filters),
    enabled: Number.isFinite(id) && id > 0,
  });

export const useOpenRecommendationsCount = () =>
  useQuery({
    queryKey: queryKeys.openRecommendationsCount,
    queryFn: () => api.listRecommendations({ status: "open", limit: 1 }),
    refetchInterval: 30_000,
    select: (data) => data.total,
  });

// --- Fan-out ---

/** Fan-out overview queries for all greenhouses at once. */
export function useAllGreenhouseOverviews(ids: number[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: queryKeys.greenhouseOverview(id),
      queryFn: () => api.greenhouseOverview(id),
      enabled: id > 0,
    })),
  });
}