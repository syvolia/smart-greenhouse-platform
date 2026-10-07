import { Grid, Stack, Typography } from "@mui/material";
import { useAllGreenhouseOverviews, useGreenhouses } from "../api/hooks";
import type { GreenhouseOverview, SensorReadingSummary } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { GreenhouseCard } from "../components/GreenhouseCard";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { formatNumber } from "../utils/format";

interface Aggregates {
  activeSensors: number;
  warningCount: number;
  criticalCount: number;
  avgTemperature: number | null;
  avgHumidity: number | null;
  avgSoilMoisture: number | null;
  openAlerts: number;
  criticalAlerts: number;
  openRecommendations: number;
  highPriorityRecommendations: number;
}

function isActiveSensors(s: SensorReadingSummary): boolean {
  return s.current_value !== null;
}

function avg(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function aggregate(overviews: GreenhouseOverview[]): Aggregates {
  let activeSensors = 0;
  let warningCount = 0;
  let criticalCount = 0;
  let openAlerts = 0;
  let criticalAlerts = 0;
  let openRecommendations = 0;
  let highPriorityRecommendations = 0;
  const temps: number[] = [];
  const hums: number[] = [];
  const soils: number[] = [];

  for (const gh of overviews) {
    openAlerts += gh.open_alerts_count ?? 0;
    criticalAlerts += gh.critical_alerts_count ?? 0;
    openRecommendations += gh.open_recommendations_count ?? 0;
    highPriorityRecommendations += gh.high_priority_recommendations_count ?? 0;

    for (const zone of gh.zones) {
      for (const r of zone.readings) {
        if (isActiveSensors(r)) activeSensors += 1;
        if (r.status === "warning") warningCount += 1;
        if (r.status === "critical") criticalCount += 1;
        if (r.current_value !== null) {
          if (r.sensor_type === "temperature") temps.push(r.current_value);
          if (r.sensor_type === "humidity") hums.push(r.current_value);
          if (r.sensor_type === "soil_moisture") soils.push(r.current_value);
        }
      }
    }
  }

  return {
    activeSensors,
    warningCount,
    criticalCount,
    avgTemperature: avg(temps),
    avgHumidity: avg(hums),
    avgSoilMoisture: avg(soils),
    openAlerts,
    criticalAlerts,
    openRecommendations,
    highPriorityRecommendations,
  };
}

export function DashboardPage() {
  const greenhousesQuery = useGreenhouses();
  const greenhouses = greenhousesQuery.data ?? [];
  const overviewsQueries = useAllGreenhouseOverviews(
    greenhouses.map((g) => g.id),
  );

  const isLoading =
    greenhousesQuery.isLoading || overviewsQueries.some((q) => q.isLoading);
  const isError =
    greenhousesQuery.isError || overviewsQueries.some((q) => q.isError);
  const overviews = overviewsQueries
    .map((q) => q.data)
    .filter((d): d is GreenhouseOverview => Boolean(d));

  if (isLoading) return <LoadingState label="Loading greenhouse overview…" />;
  if (isError)
    return (
      <ErrorState
        message="Could not load dashboard data."
        onRetry={() => {
          greenhousesQuery.refetch();
          overviewsQueries.forEach((q) => q.refetch());
        }}
      />
    );

  if (greenhouses.length === 0) {
    return (
      <EmptyState
        title="No greenhouses"
        message="Seed the backend to see data here."
      />
    );
  }

  const stats = aggregate(overviews);

  return (
    <Stack spacing={3}>
      <section aria-label="Key metrics">
        <Typography variant="h2" component="h2" gutterBottom>
          Overview
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard label="Greenhouses" value={greenhouses.length} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard label="Active sensors" value={stats.activeSensors} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard label="Warnings" value={stats.warningCount} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard label="Critical" value={stats.criticalCount} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard label="Open alerts" value={stats.openAlerts} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard label="Critical alerts" value={stats.criticalAlerts} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              label="Open recommendations"
              value={stats.openRecommendations}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              label="High-priority recommendations"
              value={stats.highPriorityRecommendations}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <MetricCard
              label="Avg temperature"
              value={formatNumber(stats.avgTemperature)}
              unit="°C"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <MetricCard
              label="Avg humidity"
              value={formatNumber(stats.avgHumidity)}
              unit="%"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <MetricCard
              label="Avg soil moisture"
              value={formatNumber(stats.avgSoilMoisture)}
              unit="%"
            />
          </Grid>
        </Grid>
      </section>

      <section aria-label="Greenhouses">
        <Typography variant="h2" component="h2" gutterBottom>
          Greenhouses
        </Typography>
        <Grid container spacing={2}>
          {greenhouses.map((g) => (
            <Grid key={g.id} item xs={12} sm={6} md={4}>
              <GreenhouseCard greenhouse={g} />
            </Grid>
          ))}
        </Grid>
      </section>
    </Stack>
  );
}
