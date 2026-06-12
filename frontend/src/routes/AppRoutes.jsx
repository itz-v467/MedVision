import { Navigate, Route, Routes } from "react-router-dom";
import { AppRoutes as Paths } from "../enums/routes";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { useAuth } from "../hooks/useAuth";
import { DashboardPage } from "../pages/DashboardPage";
import { EncountersPage } from "../pages/EncountersPage";
import { LoginPage } from "../pages/LoginPage";
import { ReviewPage } from "../pages/ReviewPage";
import { UploadPage } from "../pages/UploadPage";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to={Paths.LOGIN} replace state={{ from: "session_expired" }} />;
  }
  return children;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path={Paths.LOGIN} element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to={Paths.DASHBOARD} replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="encounters" element={<EncountersPage />} />
        <Route path="review/:encounterId" element={<ReviewPage />} />
      </Route>
      <Route path="*" element={<Navigate to={Paths.LOGIN} replace />} />
    </Routes>
  );
}
