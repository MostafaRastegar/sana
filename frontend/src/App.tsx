import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "antd";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import LoginPage from "./pages/LoginPage";
import DashboardList from "./pages/DashboardList";
import DashboardView from "./pages/DashboardView";
import ChartList from "./pages/ChartList";
import ChartBuilder from "./pages/ChartBuilder";
import DatasetList from "./pages/DatasetList";
import DatasetView from "./pages/DatasetView";
import SQLEditor from "./pages/SQLEditor";
import { isAuthenticated } from "./api/client";

const { Content } = Layout;

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout className="h-screen">
              <Sidebar />
              <Layout>
                <TopBar />
                <Content className="p-4 overflow-auto">
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboards" replace />} />
                    <Route path="/dashboards" element={<DashboardList />} />
                    <Route path="/dashboards/:id" element={<DashboardView />} />
                    <Route path="/charts" element={<ChartList />} />
                    <Route path="/charts/new" element={<ChartBuilder />} />
                    <Route path="/charts/:id" element={<ChartBuilder />} />
                    <Route path="/datasets" element={<DatasetList />} />
                    <Route path="/datasets/:id" element={<DatasetView />} />
                    <Route path="/sql" element={<SQLEditor />} />
                  </Routes>
                </Content>
              </Layout>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
