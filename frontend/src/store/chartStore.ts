import { create } from "zustand";
import type { Chart, ChartData } from "../types";
import * as api from "../api/charts";

interface ChartState {
  charts: Chart[];
  currentChart: Chart | null;
  chartData: ChartData | null;
  loading: boolean;
  error: string | null;
  fetchCharts: () => Promise<void>;
  fetchChartById: (id: number) => Promise<void>;
  fetchChartData: (id: number) => Promise<void>;
  createChart: (chart: Partial<Chart>) => Promise<Chart | undefined>;
  updateChart: (id: number, chart: Partial<Chart>) => Promise<Chart | undefined>;
  deleteChart: (id: number) => Promise<void>;
  clearError: () => void;
}

export const useChartStore = create<ChartState>()((set) => ({
  charts: [],
  currentChart: null,
  chartData: null,
  loading: false,
  error: null,

  fetchCharts: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchCharts();
      set({ charts: data.results, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchChartById: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchChartById(id);
      set({ currentChart: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchChartData: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await api.fetchChartData(id);
      set({ chartData: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  createChart: async (chart) => {
    set({ loading: true, error: null });
    try {
      const data = await api.createChart(chart);
      set((state) => ({ charts: [...state.charts, data], loading: false }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateChart: async (id, chart) => {
    set({ loading: true, error: null });
    try {
      const data = await api.updateChart(id, chart);
      set((state) => ({
        charts: state.charts.map((c) => (c.id === id ? data : c)),
        currentChart: data,
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteChart: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteChart(id);
      set((state) => ({
        charts: state.charts.filter((c) => c.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));