export type GreenhouseStatus = "active" | "inactive" | "maintenance";
export type SensorStatus = "active" | "inactive" | "maintenance" | "error";
export type SensorType =
  | "temperature"
  | "humidity"
  | "soil_moisture"
  | "light"
  | "co2"
  | "irrigation";
export type EnvironmentalStatus = "normal" | "warning" | "critical" | "unknown";

export interface Greenhouse {
  id: number;
  name: string;
  location: string;
  status: GreenhouseStatus;
  created_at: string;
  updated_at: string;
}

export interface Zone {
  id: number;
  greenhouse_id: number;
  name: string;
  crop_type: string;
  target_temperature_min: number;
  target_temperature_max: number;
  target_humidity_min: number;
  target_humidity_max: number;
  target_soil_moisture_min: number;
  target_soil_moisture_max: number;
  created_at: string;
  updated_at: string;
}

export interface Sensor {
  id: number;
  zone_id: number;
  sensor_type: SensorType;
  unit: string;
  status: SensorStatus;
  created_at: string;
}

export interface SensorSummary {
  id: number;
  sensor_type: SensorType;
  unit: string;
  status: SensorStatus;
}

export interface ZoneTopology {
  id: number;
  name: string;
  crop_type: string;
  target_temperature_min: number;
  target_temperature_max: number;
  target_humidity_min: number;
  target_humidity_max: number;
  target_soil_moisture_min: number;
  target_soil_moisture_max: number;
  sensors: SensorSummary[];
}

export interface GreenhouseTopology {
  id: number;
  name: string;
  location: string;
  status: GreenhouseStatus;
  zones: ZoneTopology[];
}

export interface SensorReadingSummary {
  sensor_id: number;
  zone_id: number;
  sensor_type: SensorType;
  unit: string;
  current_value: number | null;
  last_updated: string | null;
  min_value: number | null;
  max_value: number | null;
  avg_value: number | null;
  reading_count: number;
  status: EnvironmentalStatus;
  target_min: number | null;
  target_max: number | null;
  deviation_percent: number | null;
}

export interface ZoneOverview {
  zone_id: number;
  greenhouse_id: number;
  name: string;
  crop_type: string;
  overall_status: EnvironmentalStatus;
  readings: SensorReadingSummary[];
}

export interface GreenhouseOverview {
  greenhouse_id: number;
  name: string;
  location: string;
  overall_status: EnvironmentalStatus;
  window_start: string;
  window_end: string;
  zones: ZoneOverview[];
  open_alerts_count: number;
  critical_alerts_count: number;
  open_recommendations_count: number;
  high_priority_recommendations_count: number;
}

export interface LatestReading {
  sensor_id: number;
  zone_id: number;
  sensor_type: SensorType;
  unit: string;
  value: number;
  timestamp: string;
}

export interface LatestReadingsResponse {
  greenhouse_id: number;
  readings: LatestReading[];
}

export interface ReadingOut {
  id: number;
  sensor_id: number;
  timestamp: string;
  value: number;
}

export interface HistoryResponse {
  readings: ReadingOut[];
  count: number;
  limit: number;
  offset: number;
  start_time: string | null;
  end_time: string | null;
}

// --- Alerts (Phase 6) ---

export type AlertType = "threshold_high" | "threshold_low" | "anomaly";
export type AlertSeverity = "info" | "warning" | "critical";
export type AlertStatus = "open" | "acknowledged" | "resolved";

export interface Alert {
  id: number;
  greenhouse_id: number;
  zone_id: number | null;
  sensor_id: number | null;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  message: string;
  value: number | null;
  threshold: string | null;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

export interface AlertListResponse {
  alerts: Alert[];
  total: number;
  limit: number;
  offset: number;
}

// --- Recommendations (Phase 10) ---

export type RecommendationType =
  | "irrigation_needed"
  | "temperature_high"
  | "temperature_low"
  | "humidity_high_risk"
  | "co2_out_of_range"
  | "anomaly_review"
  | "yield_risk";

export type RecommendationPriority = "low" | "medium" | "high" | "critical";
export type RecommendationStatus = "open" | "dismissed" | "completed";

export interface Recommendation {
  id: number;
  greenhouse_id: number;
  zone_id: number | null;
  sensor_id: number | null;
  recommendation_type: RecommendationType;
  priority: RecommendationPriority;
  status: RecommendationStatus;
  message: string;
  reason: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface RecommendationListResponse {
  recommendations: Recommendation[];
  total: number;
  limit: number;
  offset: number;
}

export type UserRole = "admin" | "manager" | "agronomist" | "viewer";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}