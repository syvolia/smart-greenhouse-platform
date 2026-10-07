import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

export interface MetricCardProps {
  label: string;
  value: ReactNode;
  unit?: string;
  hint?: string;
}

export function MetricCard({ label, value, unit, hint }: MetricCardProps) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }} component="section">
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h2" component="p" sx={{ mt: 0.5 }}>
          {value}
          {unit ? (
            <Typography
              component="span"
              variant="body1"
              sx={{ ml: 0.5 }}
              color="text.secondary"
            >
              {unit}
            </Typography>
          ) : null}
        </Typography>
        {hint ? (
          <Typography variant="caption" color="text.secondary">
            {hint}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}
