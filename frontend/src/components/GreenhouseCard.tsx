import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";
import type { Greenhouse } from "../api/types";
import { StatusBadge } from "./StatusBadge";

export function GreenhouseCard({ greenhouse }: { greenhouse: Greenhouse }) {
  return (
    <Card variant="outlined" component="article">
      <CardActionArea
        component={RouterLink}
        to={`/greenhouses/${greenhouse.id}`}
        aria-label={`Open ${greenhouse.name}`}
      >
        <CardContent>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="flex-start"
          >
            <Typography variant="h4" component="h3">
              {greenhouse.name}
            </Typography>
            <StatusBadge status={greenhouse.status} />
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {greenhouse.location}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
