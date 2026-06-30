import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { AppLayout } from "./layouts/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { OrdersPage } from "./pages/OrdersPage";
import { OrderDetailPage } from "./pages/OrderDetailPage";
import { NewOrderPage } from "./pages/NewOrderPage";
import { InboxPage } from "./pages/InboxPage";
import { ValidationQueuePage } from "./pages/ValidationQueuePage";
import { AdminPage } from "./pages/AdminPage";
import { AuditLogsPage } from "./pages/AuditLogsPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="orders/new" element={<NewOrderPage />} />
        <Route path="orders/:id" element={<OrderDetailPage />} />
        <Route path="inbox" element={<InboxPage />} />
        <Route path="queue" element={<ValidationQueuePage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="audit" element={<AuditLogsPage />} />
      </Route>
    </Routes>
  );
}
