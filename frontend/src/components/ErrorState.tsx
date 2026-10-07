import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load this data. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <Alert severity="error" role="alert" sx={{ my: 2 }}>
      <AlertTitle>{title}</AlertTitle>
      <Stack spacing={1}>
        <span>{message}</span>
        {onRetry && (
          <Button
            size="small"
            onClick={onRetry}
            variant="outlined"
            color="error"
          >
            Retry
          </Button>
        )}
      </Stack>
    </Alert>
  );
}
