import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import { AlertsPage } from "./pages/AlertsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { GreenhouseDetailsPage } from "./pages/GreenhouseDetailsPage";
import { LoginPage } from "./pages/LoginPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { SensorDetailsPage } from "./pages/SensorDetailsPage";
import { ZoneDetailsPage } from "./pages/ZoneDetailsPage";

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route
              path="greenhouses/:greenhouseId"
              element={<GreenhouseDetailsPage />}
            />
            <Route path="zones/:zoneId" element={<ZoneDetailsPage />} />
            <Route path="sensors/:sensorId" element={<SensorDetailsPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
