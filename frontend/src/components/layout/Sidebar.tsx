import DashboardIcon from "@mui/icons-material/Dashboard";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import TipsAndUpdatesIcon from "@mui/icons-material/TipsAndUpdates";
import {
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import type { UserRole } from "../../api/types";

export const DRAWER_WIDTH = 240;

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  roles?: UserRole[]; // undefined = any authenticated user
}

const NAV: NavItem[] = [
  { label: "Dashboard", to: "/", icon: <DashboardIcon /> },
  { label: "Alerts", to: "/alerts", icon: <NotificationsActiveIcon /> },
  {
    label: "Recommendations",
    to: "/recommendations",
    icon: <TipsAndUpdatesIcon />,
  },
];

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
}

function Content({ onNavigate }: { onNavigate?: () => void }) {
  const { pathname } = useLocation();
  const { user } = useAuth();
  const visible = NAV.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  );

  return (
    <>
      <Toolbar sx={{ px: 2 }}>
        <Typography variant="h4" component="p" noWrap>
          🌱 Greenhouse
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {visible.map((item) => {
          const selected = pathname === item.to;
          return (
            <ListItemButton
              key={item.to}
              component={RouterLink}
              to={item.to}
              selected={selected}
              onClick={onNavigate}
              aria-current={selected ? "page" : undefined}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>
    </>
  );
}

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  return (
    <>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH },
        }}
      >
        <Content onNavigate={onClose} />
      </Drawer>
      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: "none", md: "block" },
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            boxSizing: "border-box",
          },
        }}
      >
        <Content />
      </Drawer>
    </>
  );
}
