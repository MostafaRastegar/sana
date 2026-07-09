import client from "./client";
import type {
  Dashboard,
  DashboardPermission,
  DashboardPermissionLevel,
  UserSearchResult,
} from "../types";

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

export const updateDashboardFilters = async (
  id: number,
  filters: Record<string, unknown>[]
) => {
  const { data } = await client.put(`/dashboards/${id}/filters/`, {
    filters,
  });
  return data as Dashboard;
};

export const deleteDashboard = async (id: number) => {
  await client.delete(`/dashboards/${id}/`);
};

export const renderDashboard = async (
  id: number,
  globalFilters?: Record<string, unknown>[]
) => {
  const params = globalFilters
    ? { global_filters: JSON.stringify(globalFilters) }
    : {};
  const { data } = await client.get(`/dashboards/${id}/render/`, { params });
  return data;
};

// --- Sharing & Permissions ---

export const fetchDashboardPermissions = async (id: number) => {
  const { data } = await client.get(`/dashboards/${id}/permissions/`);
  return data as DashboardPermission[];
};

export const shareDashboard = async (
  dashboardId: number,
  userId: number,
  permission: DashboardPermissionLevel
) => {
  const { data } = await client.post(`/dashboards/${dashboardId}/permissions/`, {
    user: userId,
    permission,
  });
  return data as DashboardPermission;
};

export const unshareDashboard = async (dashboardId: number, permissionId: number) => {
  await client.delete(`/dashboards/${dashboardId}/permissions/`, {
    data: { id: permissionId },
  });
};

export const toggleDashboardPublic = async (id: number, isPublic: boolean) => {
  const { data } = await client.patch(`/dashboards/${id}/`, { is_public: isPublic });
  return data as Dashboard;
};

export const searchUsers = async (query: string) => {
  const { data } = await client.get(`/users/search/`, { params: { q: query } });
  return data as UserSearchResult[];
};
