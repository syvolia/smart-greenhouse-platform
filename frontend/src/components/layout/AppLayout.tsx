import { useState } from "react";
import { Box, Toolbar } from "@mui/material";
import { Outlet, useLocation } from "react-router-dom";
import { DRAWER_WIDTH, Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

function titleFor(pathname: string): string {
  if (pathname === "/" || pathname === "") return "Dashboard";
  if (pathname.startsWith("/greenhouses")) return "Greenhouse";
  if (pathname.startsWith("/zones")) return "Zone";
  if (pathname.startsWith("/sensors")) return "Sensor";
  return "Smart Greenhouse";
}

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { pathname } = useLocation();

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <TopBar
        onMenuClick={() => setMobileOpen(true)}
        title={titleFor(pathname)}
      />
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
