import client from "./client";
import type { Chart, ChartData } from "../types";

export const fetchCharts = async (params?: Record<string, unknown>) => {
  const { data } = await client.get("/charts/", { params });
  return data as { count: number; results: Chart[] };
};

export const fetchChartById = async (id: number) => {
  const { data } = await client.get(`/charts/${id}/`);
  return data as Chart;
};

export const fetchChartData = async (id: number) => {
  const { data } = await client.get(`/charts/${id}/data/`);
  return data as ChartData;
};

export const createChart = async (chart: Partial<Chart>) => {
  const { data } = await client.post("/charts/", chart);
  return data as Chart;
};

export const previewChartData = async (dataset: number, config: Record<string, unknown>, chartType: string) => {
  const { data } = await client.post("/charts/preview/", { dataset, config, chart_type: chartType });
  return data as ChartData;
};

export const updateChart = async (id: number, chart: Partial<Chart>) => {
  const { data } = await client.put(`/charts/${id}/`, chart);
  return data as Chart;
};

export const deleteChart = async (id: number) => {
  await client.delete(`/charts/${id}/`);
};