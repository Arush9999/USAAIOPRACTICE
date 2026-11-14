import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { Layout } from "./Layout";
import { LoginPage, SignupPage, AuthCallbackPage } from "./pages/AuthPages";
import { LearnPage } from "./pages/LearnPage";
import { ModulePage } from "./pages/ModulePage";
import { PracticePage } from "./pages/PracticePage";
import { SettingsPage } from "./pages/SettingsPage";

function ProtectedLayout() {
  const { token, loading } = useAuth();
  if (loading) return <p className="route-loading">Loading your account…</p>;
  return token ? <Layout /> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route element={<ProtectedLayout />}>
        <Route index element={<Navigate to="/learn" replace />} />
        <Route path="learn" element={<LearnPage />} />
        <Route path="learn/:slug" element={<ModulePage />} />
        <Route path="practice" element={<PracticePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/learn" replace />} />
      </Route>
    </Routes>
  );
}
