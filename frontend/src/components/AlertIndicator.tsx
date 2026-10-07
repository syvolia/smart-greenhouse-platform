import NotificationsIcon from "@mui/icons-material/Notifications";
import Badge from "@mui/material/Badge";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import { Link as RouterLink } from "react-router-dom";
import { useOpenAlertsCount } from "../api/hooks";

export function AlertIndicator() {
  const { data: count = 0 } = useOpenAlertsCount();
  return (
    <Tooltip title={`${count} open alert${count === 1 ? "" : "s"}`}>
      <IconButton
        component={RouterLink}
        to="/alerts"
        aria-label={`Alerts, ${count} open`}
        color="inherit"
      >
        <Badge badgeContent={count} color="error" max={99}>
          <NotificationsIcon />
        </Badge>
      </IconButton>
    </Tooltip>
  );
}
