import client from "./client";
import type { Dataset, DatasetData } from "../types";

export const fetchDatasets = async (params?: Record<string, unknown>) => {
  const { data } = await client.get("/datasets/", { params });
  return data as { count: number; results: Dataset[] };
};

export const fetchDatasetById = async (id: number) => {
  const { data } = await client.get(`/datasets/${id}/`);
  return data as Dataset;
};

export const fetchDatasetData = async (
  id: number,
  params?: { page?: number; page_size?: number }
) => {
  const { data } = await client.get(`/datasets/${id}/data/`, { params });
  return data as DatasetData;
};

export const createDataset = async (dataset: Partial<Dataset>) => {
  const { data } = await client.post("/datasets/", dataset);
  return data as Dataset;
};

export const updateDataset = async (id: number, dataset: Partial<Dataset>) => {
  const { data } = await client.put(`/datasets/${id}/`, dataset);
  return data as Dataset;
};

export const deleteDataset = async (id: number) => {
  await client.delete(`/datasets/${id}/`);
};

export const fetchTables = async () => {
  const { data } = await client.get("/tables/");
  return data as { tables: string[] };
};

export const detectTableColumns = async (tableName: string) => {
  const { data } = await client.get(`/tables/${encodeURIComponent(tableName)}/columns/`);
  return data as { columns: { name: string; type: string; label: string }[] };
};