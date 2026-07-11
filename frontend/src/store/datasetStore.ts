import { create } from "zustand";
import type { Dataset, DatasetData } from "../types";
import * as api from "../api/datasets";

interface DatasetState {
  datasets: Dataset[];
  currentDataset: Dataset | null;
  datasetData: DatasetData | null;
  loading: boolean;
  error: string | null;
  fetchDatasets: () => Promise<void>;
  fetchDatasetById: (id: number) => Promise<void>;
  fetchDatasetData: (id: number, page?: number, pageSize?: number) => Promise<void>;
  createDataset: (dataset: Partial<Dataset>) => Promise<Dataset | undefined>;
  updateDataset: (id: number, dataset: Partial<Dataset>) => Promise<Dataset | undefined>;
  deleteDataset: (id: number) => Promise<void>;
  createFromDatasource: (datasourceId: number) => Promise<Dataset | undefined>;
  clearError: () => void;
}

export const useDatasetStore = create<DatasetState>()((set) => ({
  datasets: [],
  currentDataset: null,
  datasetData: null,
  loading: false,
  error: null,

  fetchDatasets: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDatasets();
      set({ datasets: data.results, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchDatasetById: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDatasetById(id);
      set({ currentDataset: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchDatasetData: async (id, page, pageSize) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchDatasetData(id, { page, page_size: pageSize });
      set({ datasetData: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  createDataset: async (dataset) => {
    set({ loading: true, error: null });
    try {
      const data = await api.createDataset(dataset);
      set((state) => ({ datasets: [...state.datasets, data], loading: false }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateDataset: async (id, dataset) => {
    set({ loading: true, error: null });
    try {
      const data = await api.updateDataset(id, dataset);
      set((state) => ({
        datasets: state.datasets.map((d) => (d.id === id ? data : d)),
        currentDataset: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteDataset: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteDataset(id);
      set((state) => ({
        datasets: state.datasets.filter((d) => d.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  createFromDatasource: async (datasourceId) => {
    set({ loading: true, error: null });
    try {
      const data = await api.createDatasetFromDatasource(datasourceId);
      set((state) => ({
        datasets: [...state.datasets, data],
        currentDataset: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
