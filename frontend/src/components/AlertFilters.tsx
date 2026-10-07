import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { AlertSeverity, AlertStatus } from "../api/types";

export interface AlertFilterState {
  severity: AlertSeverity | "";
  status: AlertStatus | "";
  greenhouseId: number | "";
}

export interface AlertFiltersProps {
  value: AlertFilterState;
  onChange: (next: AlertFilterState) => void;
  greenhouses: { id: number; name: string }[];
}

export function AlertFilters({
  value,
  onChange,
  greenhouses,
}: AlertFiltersProps) {
  return (
    <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
      <TextField
        select
        size="small"
        label="Severity"
        value={value.severity}
        onChange={(e) =>
          onChange({ ...value, severity: e.target.value as AlertSeverity | "" })
        }
        sx={{ minWidth: 160 }}
      >
        <MenuItem value="">All</MenuItem>
        <MenuItem value="info">Info</MenuItem>
        <MenuItem value="warning">Warning</MenuItem>
        <MenuItem value="critical">Critical</MenuItem>
      </TextField>

      <TextField
        select
        size="small"
        label="Status"
        value={value.status}
        onChange={(e) =>
          onChange({ ...value, status: e.target.value as AlertStatus | "" })
        }
        sx={{ minWidth: 160 }}
      >
        <MenuItem value="">All</MenuItem>
        <MenuItem value="open">Open</MenuItem>
        <MenuItem value="acknowledged">Acknowledged</MenuItem>
        <MenuItem value="resolved">Resolved</MenuItem>
      </TextField>

      <TextField
        select
        size="small"
        label="Greenhouse"
        value={value.greenhouseId}
        onChange={(e) =>
          onChange({
            ...value,
            greenhouseId: e.target.value === "" ? "" : Number(e.target.value),
          })
        }
        sx={{ minWidth: 200 }}
      >
        <MenuItem value="">All</MenuItem>
        {greenhouses.map((g) => (
          <MenuItem key={g.id} value={g.id}>
            {g.name}
          </MenuItem>
        ))}
      </TextField>
    </Stack>
  );
}
