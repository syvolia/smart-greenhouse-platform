import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import Stack from "@mui/material/Stack";
import { useGreenhouseAlerts } from "../api/hooks";

export function AlertBanner({ greenhouseId }: { greenhouseId: number }) {
  const { data } = useGreenhouseAlerts(greenhouseId, {
    status: "open",
    limit: 10,
  });
  const alerts = data?.alerts ?? [];
  const critical = alerts.filter((a) => a.severity === "critical");
  const warning = alerts.filter((a) => a.severity === "warning");

  if (alerts.length === 0) return null;

  return (
    <Stack spacing={1}>
      {critical.length > 0 && (
        <Alert severity="error" role="alert">
          <AlertTitle>
            {critical.length} critical alert{critical.length === 1 ? "" : "s"}
          </AlertTitle>
          {critical.slice(0, 3).map((a) => (
            <div key={a.id}>{a.message}</div>
          ))}
        </Alert>
      )}
      {warning.length > 0 && (
        <Alert severity="warning" role="alert">
          <AlertTitle>
            {warning.length} warning{warning.length === 1 ? "" : "s"}
          </AlertTitle>
          {warning.slice(0, 3).map((a) => (
            <div key={a.id}>{a.message}</div>
          ))}
        </Alert>
      )}
    </Stack>
  );
}
