import { useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Button, Grid, Stack, Typography } from "@mui/material";
import { useSensorHistory } from "../api/hooks";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { SensorChart } from "../components/SensorChart";
import { StatusBadge } from "../components/StatusBadge";
import { SENSOR_COLORS, formatNumber, formatTimestamp } from "../utils/format";

type Window = { label: string; hours: number };
const WINDOWS: Window[] = [
  { label: "1h", hours: 1 },
  { label: "6h", hours: 6 },
  { label: "24h", hours: 24 },
  { label: "7d", hours: 24 * 7 },
];

export function SensorDetailsPage() {
  const { sensorId } = useParams<{ sensorId: string }>();
  const id = Number(sensorId);
  const [hours, setHours] = useState(1);

  const end = new Date();
  const start = new Date(end.getTime() - hours * 3600 * 1000);

  const history = useSensorHistory(id, {
    start_time: start.toISOString(),
    end_time: end.toISOString(),
    limit: 5000,
  });

  if (history.isLoading) return <LoadingState label="Loading sensor…" />;
  if (history.isError)
    return (
      <ErrorState
        message="Could not load sensor history."
        onRetry={() => history.refetch()}
      />
    );

  const readings = history.data?.readings ?? [];
  const values = readings.map((r) => r.value);
  const min = values.length ? Math.min(...values) : null;
  const max = values.length ? Math.max(...values) : null;
  const avg = values.length
    ? values.reduce((a, b) => a + b, 0) / values.length
    : null;
  const latest = readings[0];

  return (
    <Stack spacing={3}>
      <Box>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Typography variant="h2" component="h2">
            Sensor #{id}
          </Typography>
          <StatusBadge status="active" size="medium" />
        </Stack>
        {latest && (
          <Typography color="text.secondary">
            Last reading at {formatTimestamp(latest.timestamp)}
          </Typography>
        )}
      </Box>

      <Stack direction="row" spacing={1}>
        {WINDOWS.map((w) => (
          <Button
            key={w.label}
            size="small"
            variant={hours === w.hours ? "contained" : "outlined"}
            onClick={() => setHours(w.hours)}
            aria-pressed={hours === w.hours}
          >
            {w.label}
          </Button>
        ))}
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard label="Current" value={formatNumber(latest?.value)} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard label="Min" value={formatNumber(min)} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard label="Max" value={formatNumber(max)} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard label="Average" value={formatNumber(avg)} />
        </Grid>
      </Grid>

      <section aria-label="Sensor history">
        <Typography variant="h3" component="h3" gutterBottom>
          History
        </Typography>
        {readings.length === 0 ? (
          <EmptyState
            title="No readings in this window"
            message="Try widening the time range."
          />
        ) : (
          <SensorChart
            readings={readings}
            color={SENSOR_COLORS.temperature}
            unit=""
            label="Sensor"
          />
        )}
      </section>
    </Stack>
  );
}
