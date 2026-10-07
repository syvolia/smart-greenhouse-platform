import type { EnvironmentalStatus, SensorType } from "../api/types";

export const SENSOR_LABELS: Record<SensorType, string> = {
  temperature: "Temperature",
  humidity: "Humidity",
  soil_moisture: "Soil Moisture",
  light: "Light",
  co2: "CO₂",
  irrigation: "Irrigation",
};

export const SENSOR_COLORS: Record<SensorType, string> = {
  temperature: "#d32f2f",
  humidity: "#0288d1",
  soil_moisture: "#6d4c41",
  light: "#f9a825",
  co2: "#6a1b9a",
  irrigation: "#00838f",
};

export function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function statusLabel(status: EnvironmentalStatus): string {
  switch (status) {
    case "normal": return "Normal";
    case "warning": return "Warning";
    case "critical": return "Critical";
    case "unknown": return "Unknown";
  }
}