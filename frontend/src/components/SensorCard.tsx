import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";
import type { SensorReadingSummary } from "../api/types";
import { SENSOR_LABELS, formatNumber, formatTimestamp } from "../utils/format";
import { StatusBadge } from "./StatusBadge";

export function SensorCard({ summary }: { summary: SensorReadingSummary }) {
  return (
    <Card variant="outlined" component="article">
      <CardActionArea
        component={RouterLink}
        to={`/sensors/${summary.sensor_id}`}
        aria-label={`Open ${SENSOR_LABELS[summary.sensor_type]} sensor`}
      >
        <CardContent>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="flex-start"
          >
            <Typography variant="h4" component="h3">
              {SENSOR_LABELS[summary.sensor_type]}
            </Typography>
            <StatusBadge status={summary.status} />
          </Stack>
          <Typography variant="h3" component="p" sx={{ mt: 1 }}>
            {formatNumber(summary.current_value)}
            <Typography
              component="span"
              variant="body2"
              sx={{ ml: 0.5 }}
              color="text.secondary"
            >
              {summary.unit}
            </Typography>
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Updated: {formatTimestamp(summary.last_updated)}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
