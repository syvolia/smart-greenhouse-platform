import { useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Grid, Stack, Typography } from "@mui/material";
import { useZoneOverview } from "../api/hooks";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { SensorCard } from "../components/SensorCard";
import { StatusBadge } from "../components/StatusBadge";
import { formatNumber } from "../utils/format";


export function ZoneDetailsPage() {
  const { zoneId } = useParams<{ zoneId: string }>();
  const id = Number(zoneId);
  const overview = useZoneOverview(id);
  const [focusedSensorId] = useState<number | null>(null);

  if (overview.isLoading) return <LoadingState label="Loading zone…" />;
  if (overview.isError)
    return (
      <ErrorState
        message="Could not load zone."
        onRetry={() => overview.refetch()}
      />
    );
  if (!overview.data) return <EmptyState title="Zone not found" />;

  const z = overview.data;

  return (
    <Stack spacing={3}>
      <Box>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Typography variant="h2" component="h2">
            {z.name}
          </Typography>
          <StatusBadge status={z.overall_status} size="medium" />
        </Stack>
        <Typography color="text.secondary">
          Crop: {z.crop_type} · Greenhouse {z.greenhouse_id}
        </Typography>
      </Box>

      <Grid container spacing={2}>
        {z.readings.map((r) => (
          <Grid key={r.sensor_id} item xs={12} sm={6} md={4}>
            <SensorCard summary={r} />
          </Grid>
        ))}
      </Grid>

      <section aria-label="Targets and current values">
        <Typography variant="h3" component="h3" gutterBottom>
          Targets
        </Typography>
        <Grid container spacing={2}>
          {z.readings.map((r) => (
            <Grid key={r.sensor_id} item xs={12} sm={6} md={4}>
              <MetricCard
                label={`${r.sensor_type} target`}
                value={
                  r.target_min !== null && r.target_max !== null
                    ? `${formatNumber(r.target_min)} – ${formatNumber(
                        r.target_max,
                      )}`
                    : "No target"
                }
                unit={r.unit}
                hint={
                  r.deviation_percent !== null && r.deviation_percent !== 0
                    ? `Deviation: ${formatNumber(r.deviation_percent)}%`
                    : undefined
                }
              />
            </Grid>
          ))}
        </Grid>
        {focusedSensorId === null ? null : (
          <Typography variant="caption" color="text.secondary">
            Focused sensor: {focusedSensorId}
          </Typography>
        )}
      </section>
    </Stack>
  );
}
