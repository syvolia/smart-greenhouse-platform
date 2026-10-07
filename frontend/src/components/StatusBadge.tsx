import Chip from "@mui/material/Chip";
import type {
  EnvironmentalStatus,
  GreenhouseStatus,
  SensorStatus,
} from "../api/types";

type AnyStatus = EnvironmentalStatus | GreenhouseStatus | SensorStatus;

const COLORS: Record<
  AnyStatus,
  "success" | "warning" | "error" | "default" | "info"
> = {
  normal: "success",
  active: "success",
  warning: "warning",
  maintenance: "warning",
  critical: "error",
  error: "error",
  inactive: "default",
  unknown: "default",
};

const LABELS: Record<AnyStatus, string> = {
  normal: "Normal",
  active: "Active",
  warning: "Warning",
  maintenance: "Maintenance",
  critical: "Critical",
  error: "Error",
  inactive: "Inactive",
  unknown: "Unknown",
};

export interface StatusBadgeProps {
  status: AnyStatus;
  size?: "small" | "medium";
}

/**
 * Accessible status chip.
 * Never communicates status via color alone: the label text is always present
 * and the aria-label spells out the full phrase for screen readers.
 */
export function StatusBadge({ status, size = "small" }: StatusBadgeProps) {
  const label = LABELS[status];
  return (
    <Chip
      size={size}
      color={COLORS[status]}
      label={label}
      aria-label={`Status: ${label}`}
      variant={
        status === "unknown" || status === "inactive" ? "outlined" : "filled"
      }
    />
  );
}
