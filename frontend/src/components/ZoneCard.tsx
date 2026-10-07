import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";
import type { ZoneTopology } from "../api/types";
import { StatusBadge } from "./StatusBadge";

export interface ZoneCardProps {
  zone: ZoneTopology;
  overallStatus?: "normal" | "warning" | "critical" | "unknown";
}

export function ZoneCard({ zone, overallStatus = "unknown" }: ZoneCardProps) {
  return (
    <Card variant="outlined" component="article">
      <CardActionArea
        component={RouterLink}
        to={`/zones/${zone.id}`}
        aria-label={`Open ${zone.name}`}
      >
        <CardContent>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="flex-start"
          >
            <Typography variant="h4" component="h3">
              {zone.name}
            </Typography>
            <StatusBadge status={overallStatus} />
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Crop: {zone.crop_type}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Sensors: {zone.sensors.length}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
