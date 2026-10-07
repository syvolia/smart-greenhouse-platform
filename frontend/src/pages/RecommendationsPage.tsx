import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Box, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { api } from "../api/client";
import { useGreenhouses, useRecommendations } from "../api/hooks";
import type {
  RecommendationPriority,
  RecommendationStatus,
} from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { RecommendationCard } from "../components/RecommendationCard";

interface FilterState {
  status: RecommendationStatus | "";
  priority: RecommendationPriority | "";
  greenhouseId: number | "";
}

export function RecommendationsPage() {
  const [filters, setFilters] = useState<FilterState>({
    status: "open",
    priority: "",
    greenhouseId: "",
  });
  const [busyId, setBusyId] = useState<number | null>(null);
  const qc = useQueryClient();
  const greenhouses = useGreenhouses();

  const queryFilters = useMemo(
    () => ({
      status: (filters.status || undefined) as RecommendationStatus | undefined,
      priority: (filters.priority || undefined) as
        | RecommendationPriority
        | undefined,
      greenhouse_id: filters.greenhouseId || undefined,
      limit: 100,
    }),
    [filters],
  );

  const recs = useRecommendations(queryFilters);

  const dismiss = useMutation({
    mutationFn: (id: number) => api.dismissRecommendation(id),
    onMutate: (id) => setBusyId(id),
    onSettled: () => {
      setBusyId(null);
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });

  const complete = useMutation({
    mutationFn: (id: number) => api.completeRecommendation(id),
    onMutate: (id) => setBusyId(id),
    onSettled: () => {
      setBusyId(null);
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h2" component="h2" gutterBottom>
          Recommendations
        </Typography>
        <Typography color="text.secondary">
          Actionable guidance derived from live sensor data, alerts, and ML
          predictions.
        </Typography>
      </Box>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          select
          size="small"
          label="Status"
          value={filters.status}
          onChange={(e) =>
            setFilters({
              ...filters,
              status: e.target.value as RecommendationStatus | "",
            })
          }
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="open">Open</MenuItem>
          <MenuItem value="dismissed">Dismissed</MenuItem>
          <MenuItem value="completed">Completed</MenuItem>
        </TextField>
        <TextField
          select
          size="small"
          label="Priority"
          value={filters.priority}
          onChange={(e) =>
            setFilters({
              ...filters,
              priority: e.target.value as RecommendationPriority | "",
            })
          }
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="low">Low</MenuItem>
          <MenuItem value="medium">Medium</MenuItem>
          <MenuItem value="high">High</MenuItem>
          <MenuItem value="critical">Critical</MenuItem>
        </TextField>
        <TextField
          select
          size="small"
          label="Greenhouse"
          value={filters.greenhouseId}
          onChange={(e) =>
            setFilters({
              ...filters,
              greenhouseId: e.target.value === "" ? "" : Number(e.target.value),
            })
          }
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="">All</MenuItem>
          {(greenhouses.data ?? []).map((g) => (
            <MenuItem key={g.id} value={g.id}>
              {g.name}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {recs.isLoading ? (
        <LoadingState label="Loading recommendations…" />
      ) : recs.isError ? (
        <ErrorState
          message="Could not load recommendations."
          onRetry={() => recs.refetch()}
        />
      ) : (recs.data?.recommendations.length ?? 0) === 0 ? (
        <EmptyState
          title="No recommendations match"
          message="The engine runs after every ingestion cycle — check back soon."
        />
      ) : (
        <Stack spacing={2}>
          {recs.data!.recommendations.map((r) => (
            <RecommendationCard
              key={r.id}
              recommendation={r}
              busy={busyId === r.id}
              onDismiss={(id) => dismiss.mutate(id)}
              onComplete={(id) => complete.mutate(id)}
            />
          ))}
        </Stack>
      )}
    </Stack>
  );
}
