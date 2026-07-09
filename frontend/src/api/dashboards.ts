import client from "./client";
import type { Dashboard } from "../types";

export const fetchDashboards = async (params?: Record<string, unknown>) => {
  const { data } = await client.get("/dashboards/", { params });
  return data as { count: number; results: Dashboard[] };
};

export const fetchDashboardById = async (id: number) => {
  const { data } = await client.get(`/dashboards/${id}/`);
  return data as Dashboard;
};

export const createDashboard = async (dashboard: Partial<Dashboard>) => {
  const { data } = await client.post("/dashboards/", dashboard);
  return data as Dashboard;
};

export const updateDashboard = async (
  id: number,
  dashboard: Partial<Dashboard>
) => {
  const { data } = await client.put(`/dashboards/${id}/`, dashboard);
  return data as Dashboard;
};

export const updateDashboardLayout = async (
  id: number,
  layout: Record<string, unknown>
) => {
  const { data } = await client.put(`/dashboards/${id}/layout/`, {
    layout,
  });
  return data as Dashboard;
};

export const deleteDashboard = async (id: number) => {
  await client.delete(`/dashboards/${id}/`);
};

export const renderDashboard = async (id: number) => {
  const { data } = await client.get(`/dashboards/${id}/render/`);
  return data;
};