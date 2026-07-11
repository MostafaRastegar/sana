import { create } from "zustand";
import type { DataSource, SyncLog } from "../types";
import * as api from "../api/datasources";

interface DatasourceState {
  datasources: DataSource[];
  currentDatasource: DataSource | null;
  logs: SyncLog[];
  records: { columns: string[]; rows: Record<string, unknown>[]; row_count: number } | null;
  loading: boolean;
  error: string | null;
  fetchDatasources: () => Promise<void>;
  fetchDatasourceById: (id: number) => Promise<void>;
  createDatasource: (ds: Partial<DataSource>) => Promise<DataSource | undefined>;
  updateDatasource: (id: number, ds: Partial<DataSource>) => Promise<DataSource | undefined>;
  deleteDatasource: (id: number) => Promise<void>;
  testConnection: (id: number) => Promise<{ success: boolean; message: string } | undefined>;
  sync: (id: number) => Promise<void>;
  fetchLogs: (id: number) => Promise<void>;
  fetchRecords: (id: number) => Promise<void>;
  clearError: () => void;
}

export const useDatasourceStore = create<DatasourceState>()((set) => ({
  datasources: [],
  currentDatasource: null,
  logs: [],
  records: null,
  loading: false,
  error: null,

  fetchDatasources: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDataSources();
      set({ datasources: data.results, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchDatasourceById: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDataSourceById(id);
      set({ currentDatasource: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  createDatasource: async (ds) => {
    set({ loading: true, error: null });
    try {
      const data = await api.createDataSource(ds);
      set((state) => ({ datasources: [...state.datasources, data], loading: false }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateDatasource: async (id, ds) => {
    set({ loading: true, error: null });
    try {
      const data = await api.updateDataSource(id, ds);
      set((state) => ({
        datasources: state.datasources.map((d) => (d.id === id ? data : d)),
        currentDatasource: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteDatasource: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteDataSource(id);
      set((state) => ({
        datasources: state.datasources.filter((d) => d.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  testConnection: async (id) => {
    set({ error: null });
    try {
      const result = await api.testConnection(id);
      return result;
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  sync: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.syncDataSource(id);
      // Refresh datasource and logs after sync
      const [ds, logs] = await Promise.all([
        api.fetchDataSourceById(id),
        api.fetchSyncLogs(id),
      ]);
      set((state) => ({
        datasources: state.datasources.map((d) => (d.id === id ? ds : d)),
        currentDatasource: ds,
        logs,
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchLogs: async (id) => {
    try {
      const logs = await api.fetchSyncLogs(id);
      set({ logs });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchRecords: async (id) => {
    try {
      const records = await api.fetchRecords(id);
      set({ records });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  clearError: () => set({ error: null }),
}));