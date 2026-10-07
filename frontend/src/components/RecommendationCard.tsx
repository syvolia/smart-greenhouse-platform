import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { Recommendation, RecommendationPriority } from "../api/types";
import { formatTimestamp } from "../utils/format";

const PRIORITY_COLOR: Record<
  RecommendationPriority,
  "error" | "warning" | "info" | "default"
> = {
  critical: "error",
  high: "error",
  medium: "warning",
  low: "info",
};

const TYPE_LABEL: Record<string, string> = {
  irrigation_needed: "Irrigation",
  temperature_high: "High temperature",
  temperature_low: "Low temperature",
  humidity_high_risk: "Humidity / disease risk",
  co2_out_of_range: "CO₂ out of range",
  anomaly_review: "Anomaly review",
  yield_risk: "Yield risk",
};

export interface RecommendationCardProps {
  recommendation: Recommendation;
  onDismiss?: (id: number) => void;
  onComplete?: (id: number) => void;
  busy?: boolean;
}

export function RecommendationCard({
  recommendation,
  onDismiss,
  onComplete,
  busy,
}: RecommendationCardProps) {
  const rec = recommendation;
  return (
    <Card variant="outlined" component="article">
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
          <Chip
            size="small"
            color={PRIORITY_COLOR[rec.priority]}
            label={rec.priority}
          />
          <Chip
            size="small"
            variant="outlined"
            label={
              TYPE_LABEL[rec.recommendation_type] ?? rec.recommendation_type
            }
          />
          <Typography variant="caption" color="text.secondary">
            {formatTimestamp(rec.created_at)}
          </Typography>
        </Stack>
        <Typography variant="body1" sx={{ mb: 1 }}>
          {rec.message}
        </Typography>
        <Typography
          variant="caption"
          color="text.secondary"
          display="block"
          sx={{ mb: 1 }}
        >
          Why: {rec.reason}
        </Typography>
        {rec.status === "open" && (
          <Stack direction="row" spacing={1}>
            {onComplete && (
              <Button
                size="small"
                variant="contained"
                onClick={() => onComplete(rec.id)}
                disabled={busy}
              >
                Mark completed
              </Button>
            )}
            {onDismiss && (
              <Button
                size="small"
                variant="outlined"
                onClick={() => onDismiss(rec.id)}
                disabled={busy}
              >
                Dismiss
              </Button>
            )}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
