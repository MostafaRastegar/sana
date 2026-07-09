import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import type { RouteObject } from "react-router-dom";
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

function ProtectedLayout() {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return (

<Layout className="h-screen">
        <Sidebar />
        <Layout>
          <TopBar />
          <Content className="p-4 overflow-auto">
            <Outlet />
          </Content>
        </Layout>
      </Layout>
  );
}

const routes: RouteObject[] = [
  { path: "/login", element: <LoginPage /> },
  {
    path: "/*",
    element: <ProtectedLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboards" replace /> },
      { path: "dashboards", element: <DashboardList /> },
      { path: "dashboards/:id", element: <DashboardView /> },
      { path: "charts", element: <ChartList /> },
      { path: "charts/new", element: <ChartBuilder /> },
      { path: "charts/:id", element: <ChartBuilder /> },
      { path: "datasets", element: <DatasetList /> },
      { path: "datasets/:id", element: <DatasetView /> },
      { path: "sql", element: <SQLEditor /> },
    ],
  },
];

export const router = createBrowserRouter(routes);