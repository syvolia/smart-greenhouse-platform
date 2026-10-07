import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import type { Alert, AlertSeverity } from "../api/types";
import { formatTimestamp } from "../utils/format";

const SEV_COLOR: Record<AlertSeverity, "error" | "warning" | "info"> = {
  critical: "error",
  warning: "warning",
  info: "info",
};

export interface AlertTableProps {
  alerts: Alert[];
  onAcknowledge?: (id: number) => void;
  onResolve?: (id: number) => void;
  busyId?: number | null;
}

export function AlertTable({
  alerts,
  onAcknowledge,
  onResolve,
  busyId,
}: AlertTableProps) {
  return (
    <Table size="small" aria-label="Alerts">
      <TableHead>
        <TableRow>
          <TableCell>Severity</TableCell>
          <TableCell>Status</TableCell>
          <TableCell>Type</TableCell>
          <TableCell>Location</TableCell>
          <TableCell>Message</TableCell>
          <TableCell>Value</TableCell>
          <TableCell>Created</TableCell>
          <TableCell align="right">Actions</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {alerts.map((a) => (
          <TableRow key={a.id} hover>
            <TableCell>
              <Chip
                size="small"
                color={SEV_COLOR[a.severity]}
                label={a.severity}
              />
            </TableCell>
            <TableCell>
              <Chip size="small" variant="outlined" label={a.status} />
            </TableCell>
            <TableCell>{a.alert_type}</TableCell>
            <TableCell>
              gh {a.greenhouse_id} · zone {a.zone_id ?? "–"} · sensor{" "}
              {a.sensor_id ?? "–"}
            </TableCell>
            <TableCell>{a.message}</TableCell>
            <TableCell>
              {a.value ?? "–"}{" "}
              {a.threshold ? <small>({a.threshold})</small> : null}
            </TableCell>
            <TableCell>{formatTimestamp(a.created_at)}</TableCell>
            <TableCell align="right">
              <Stack direction="row" spacing={1} justifyContent="flex-end">
                {a.status === "open" && onAcknowledge && (
                  <Button
                    size="small"
                    onClick={() => onAcknowledge(a.id)}
                    disabled={busyId === a.id}
                  >
                    Acknowledge
                  </Button>
                )}
                {a.status !== "resolved" && onResolve && (
                  <Button
                    size="small"
                    color="error"
                    onClick={() => onResolve(a.id)}
                    disabled={busyId === a.id}
                  >
                    Resolve
                  </Button>
                )}
              </Stack>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
