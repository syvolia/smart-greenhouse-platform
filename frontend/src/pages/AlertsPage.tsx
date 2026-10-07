import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Box, Paper, Stack, Typography } from "@mui/material";
import { api } from "../api/client";
import { useAlerts, useGreenhouses } from "../api/hooks";
import type { AlertSeverity, AlertStatus } from "../api/types";
import { AlertFilters, type AlertFilterState } from "../components/AlertFilters";
import { AlertTable } from "../components/AlertTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function AlertsPage() {
  const [filters, setFilters] = useState<AlertFilterState>({
    severity: "",
    status: "open",
    greenhouseId: "",
  });
  const [busyId, setBusyId] = useState<number | null>(null);

  const greenhouses = useGreenhouses();

  const queryFilters = useMemo(
    () => ({
      severity: (filters.severity || undefined) as AlertSeverity | undefined,
      status: (filters.status || undefined) as AlertStatus | undefined,
      greenhouse_id: filters.greenhouseId || undefined,
      limit: 100,
    }),
    [filters]
  );

  const alerts = useAlerts(queryFilters);
  const qc = useQueryClient();

  const ack = useMutation({
    mutationFn: (id: number) => api.acknowledgeAlert(id),
    onMutate: (id) => setBusyId(id),
    onSettled: () => {
      setBusyId(null);
      qc.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const resolve = useMutation({
    mutationFn: (id: number) => api.resolveAlert(id),
    onMutate: (id) => setBusyId(id),
    onSettled: () => {
      setBusyId(null);
      qc.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h2" component="h2" gutterBottom>
          Alerts
        </Typography>
        <Typography color="text.secondary">
          Threshold breaches and statistical anomalies across all greenhouses.
        </Typography>
      </Box>

      <AlertFilters
        value={filters}
        onChange={setFilters}
        greenhouses={greenhouses.data ?? []}
      />

      {alerts.isLoading ? (
        <LoadingState label="Loading alerts…" />
      ) : alerts.isError ? (
        <ErrorState
          message="Could not load alerts."
          onRetry={() => alerts.refetch()}
        />
      ) : (alerts.data?.alerts.length ?? 0) === 0 ? (
        <EmptyState
          title="No alerts match"
          message="Try changing filters, or wait — the engine re-evaluates every ingestion cycle."
        />
      ) : (
        <Paper variant="outlined">
          <AlertTable
            alerts={alerts.data!.alerts}
            onAcknowledge={(id) => ack.mutate(id)}
            onResolve={(id) => resolve.mutate(id)}
            busyId={busyId}
          />
        </Paper>
      )}
    </Stack>
  );
}