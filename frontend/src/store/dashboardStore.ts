import { create } from "zustand";
import type { Dashboard } from "../types";
import * as api from "../api/dashboards";

let fetchIdCounter = 0;

interface DashboardState {
  dashboards: Dashboard[];
  currentDashboard: Dashboard | null;
  loading: boolean;
  error: string | null;
  fetchDashboards: () => Promise<void>;
  fetchDashboardById: (id: number) => Promise<void>;
  createDashboard: (dashboard: Partial<Dashboard>) => Promise<Dashboard | undefined>;
  updateDashboard: (id: number, dashboard: Partial<Dashboard>) => Promise<Dashboard | undefined>;
  updateLayout: (id: number, layout: Record<string, unknown>) => Promise<Dashboard | undefined>;
  deleteDashboard: (id: number) => Promise<void>;
  clearError: () => void;
}

export const useDashboardStore = create<DashboardState>()((set, get) => ({
  dashboards: [],
  currentDashboard: null,
  loading: false,
  error: null,

  fetchDashboards: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDashboards();
      set({ dashboards: data.results, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchDashboardById: async (id) => {
    const requestId = ++fetchIdCounter;
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDashboardById(id);
      if (requestId !== fetchIdCounter) return; // stale response
      set({ currentDashboard: data, loading: false });
    } catch (error) {
      if (requestId !== fetchIdCounter) return; // stale response
      set({ error: (error as Error).message, loading: false });
    }
  },

  createDashboard: async (dashboard) => {
    set({ loading: true, error: null });
    try {
      const data = await api.createDashboard(dashboard);
      set((state) => ({ dashboards: [...state.dashboards, data], loading: false }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateDashboard: async (id, dashboard) => {
    set({ loading: true, error: null });
    try {
      const data = await api.updateDashboard(id, dashboard);
      set((state) => ({
        dashboards: state.dashboards.map((d) => (d.id === id ? data : d)),
        currentDashboard: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateLayout: async (id, layout) => {
    set({ loading: true, error: null });
    try {
      const data = await api.updateDashboardLayout(id, layout);
      set((state) => ({
        dashboards: state.dashboards.map((d) => (d.id === id ? data : d)),
        currentDashboard: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteDashboard: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteDashboard(id);
      set((state) => ({
        dashboards: state.dashboards.filter((d) => d.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));