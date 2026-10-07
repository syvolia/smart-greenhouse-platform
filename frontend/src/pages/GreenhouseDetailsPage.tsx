import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Button, Grid, Stack, Typography } from "@mui/material";
import {
  useGreenhouse,
  useGreenhouseHistory,
  useGreenhouseOverview,
  useGreenhouseRecommendations,
  useLatestReadings,
} from "../api/hooks";
import type { SensorType } from "../api/types";
import { AlertBanner } from "../components/AlertBanner";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { RecommendationCard } from "../components/RecommendationCard";
import { SensorChart } from "../components/SensorChart";
import { StatusBadge } from "../components/StatusBadge";
import { ZoneCard } from "../components/ZoneCard";
import { SENSOR_COLORS, SENSOR_LABELS, formatTimestamp } from "../utils/format";

const CHART_TYPES: SensorType[] = [
  "temperature",
  "humidity",
  "soil_moisture",
  "co2",
  "light",
];

export function GreenhouseDetailsPage() {
  const { greenhouseId } = useParams<{ greenhouseId: string }>();
  const id = Number(greenhouseId);
  const [chartType, setChartType] = useState<SensorType>("temperature");

  const gh = useGreenhouse(id);
  const overview = useGreenhouseOverview(id);
  const latest = useLatestReadings(id);
  const history = useGreenhouseHistory(id, {
    sensor_type: chartType,
    limit: 500,
  });
  const recommendations = useGreenhouseRecommendations(id, {
    status: "open",
    limit: 5,
  });

  const zoneStatusById = useMemo(() => {
    const map = new Map<
      number,
      "normal" | "warning" | "critical" | "unknown"
    >();
    overview.data?.zones.forEach((z) => map.set(z.zone_id, z.overall_status));
    return map;
  }, [overview.data]);

  if (gh.isLoading || overview.isLoading)
    return <LoadingState label="Loading greenhouse…" />;
  if (gh.isError || overview.isError)
    return (
      <ErrorState
        message="Could not load greenhouse data."
        onRetry={() => {
          gh.refetch();
          overview.refetch();
        }}
      />
    );
  if (!gh.data || !overview.data)
    return (
      <EmptyState
        title="Greenhouse not found"
        message="Check the URL or go back."
      />
    );

  const g = gh.data;
  const o = overview.data;

  return (
    <Stack spacing={3}>
      <Box>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Typography variant="h2" component="h2">
            {g.name}
          </Typography>
          <StatusBadge status={o.overall_status} size="medium" />
        </Stack>
        <Typography color="text.secondary">{g.location}</Typography>
      </Box>

      <AlertBanner greenhouseId={id} />

      {recommendations.data && recommendations.data.recommendations.length > 0 && (
        <section aria-label="Recommendations">
          <Typography variant="h3" component="h3" gutterBottom>
            Recommendations
          </Typography>
          <Stack spacing={1}>
            {recommendations.data.recommendations.map((r) => (
              <RecommendationCard key={r.id} recommendation={r} />
            ))}
          </Stack>
        </section>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <MetricCard label="Zones" value={o.zones.length} />
        </Grid>
        <Grid item xs={12} sm={4}>
          <MetricCard
            label="Latest readings"
            value={latest.data?.readings.length ?? 0}
            hint={`Window ends ${formatTimestamp(o.window_end)}`}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <MetricCard
            label="Overall status"
            value={o.overall_status.toUpperCase()}
          />
        </Grid>
      </Grid>

      <section aria-label="Zones">
        <Typography variant="h3" component="h3" gutterBottom>
          Zones
        </Typography>
        <Grid container spacing={2}>
          {o.zones.map((z) => {
            const topologyZone = {
              id: z.zone_id,
              name: z.name,
              crop_type: z.crop_type,
              target_temperature_min: 0,
              target_temperature_max: 0,
              target_humidity_min: 0,
              target_humidity_max: 0,
              target_soil_moisture_min: 0,
              target_soil_moisture_max: 0,
              sensors: [],
            };
            return (
              <Grid key={z.zone_id} item xs={12} sm={6} md={4}>
                <ZoneCard
                  zone={topologyZone}
                  overallStatus={zoneStatusById.get(z.zone_id)}
                />
              </Grid>
            );
          })}
        </Grid>
      </section>

      <section aria-label="Historical chart">
        <Typography variant="h3" component="h3" gutterBottom>
          Historical readings
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
          {CHART_TYPES.map((t) => (
            <Button
              key={t}
              variant={chartType === t ? "contained" : "outlined"}
              size="small"
              onClick={() => setChartType(t)}
              aria-pressed={chartType === t}
            >
              {SENSOR_LABELS[t]}
            </Button>
          ))}
        </Stack>
        {history.isLoading ? (
          <LoadingState label="Loading chart…" />
        ) : history.isError ? (
          <ErrorState
            message="Could not load history."
            onRetry={() => history.refetch()}
          />
        ) : (
          <SensorChart
            readings={history.data?.readings ?? []}
            color={SENSOR_COLORS[chartType]}
            unit={unitFor(chartType)}
            label={SENSOR_LABELS[chartType]}
          />
        )}
      </section>
    </Stack>
  );
}

function unitFor(t: SensorType): string {
  switch (t) {
    case "temperature":
      return "°C";
    case "humidity":
      return "%";
    case "soil_moisture":
      return "%";
    case "co2":
      return "ppm";
    case "light":
      return "lux";
    case "irrigation":
      return "L/min";
  }
}
