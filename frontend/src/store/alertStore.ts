import { create } from "zustand";
import type { DataAlert, AlertHistory, AlertStats } from "../types";
import * as api from "../api/alerts";

interface AlertState {
  alerts: DataAlert[];
  currentAlert: DataAlert | null;
  alertHistory: AlertHistory[];
  stats: AlertStats | null;
  loading: boolean;
  error: string | null;
  fetchAlerts: (params?: Record<string, unknown>) => Promise<void>;
  fetchAlertById: (id: number) => Promise<void>;
  createAlert: (alert: Partial<DataAlert>) => Promise<DataAlert | undefined>;
  updateAlert: (id: number, alert: Partial<DataAlert>) => Promise<DataAlert | undefined>;
  deleteAlert: (id: number) => Promise<void>;
  toggleAlert: (id: number) => Promise<void>;
  checkAlertNow: (id: number) => Promise<{ triggered: boolean; history?: AlertHistory; message?: string } | undefined>;
  fetchAlertHistory: (id: number) => Promise<void>;
  fetchAlertStats: () => Promise<void>;
  clearError: () => void;
}

export const useAlertStore = create<AlertState>()((set) => ({
  alerts: [],
  currentAlert: null,
  alertHistory: [],
  stats: null,
  loading: false,
  error: null,

  fetchAlerts: async (params) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchAlerts(params);
      set({ alerts: data.results, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchAlertById: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchAlertById(id);
      set({ currentAlert: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  createAlert: async (alert) => {
    set({ loading: true, error: null });
    try {
      const data = await api.createAlert(alert);
      set((state) => ({ alerts: [...state.alerts, data], loading: false }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateAlert: async (id, alert) => {
    set({ loading: true, error: null });
    try {
      const data = await api.updateAlert(id, alert);
      set((state) => ({
        alerts: state.alerts.map((a) => (a.id === id ? data : a)),
        currentAlert: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteAlert: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteAlert(id);
      set((state) => ({
        alerts: state.alerts.filter((a) => a.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  toggleAlert: async (id) => {
    try {
      const data = await api.toggleAlert(id);
      set((state) => ({
        alerts: state.alerts.map((a) => (a.id === id ? data : a)),
        currentAlert: state.currentAlert?.id === id ? data : state.currentAlert,
      }));
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  checkAlertNow: async (id) => {
    try {
      const result = await api.checkAlertNow(id);
      return result;
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchAlertHistory: async (id) => {
    try {
      const data = await api.fetchAlertHistory(id);
      set({ alertHistory: data.results });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchAlertStats: async () => {
    try {
      const data = await api.fetchAlertStats();
      set({ stats: data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  clearError: () => set({ error: null }),
}));