import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

export interface EmptyStateProps {
  title?: string;
  message?: string;
}

export function EmptyState({
  title = "No data yet",
  message = "Once readings start arriving, they will appear here.",
}: EmptyStateProps) {
  return (
    <Box role="status" sx={{ textAlign: "center", py: 6, px: 2 }}>
      <Typography variant="h4" gutterBottom>
        {title}
      </Typography>
      <Typography color="text.secondary">{message}</Typography>
    </Box>
  );
}
