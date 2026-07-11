import client from "./client";
import type { DataSource, SyncLog } from "../types";

export const fetchDataSources = async (params?: Record<string, unknown>) => {
  const { data } = await client.get("/datasources/", { params });
  return data as { count: number; results: DataSource[] };
};

export const fetchDataSourceById = async (id: number) => {
  const { data } = await client.get(`/datasources/${id}/`);
  return data as DataSource;
};

export const createDataSource = async (ds: Partial<DataSource>) => {
  const { data } = await client.post("/datasources/", ds);
  return data as DataSource;
};

export const updateDataSource = async (id: number, ds: Partial<DataSource>) => {
  const { data } = await client.put(`/datasources/${id}/`, ds);
  return data as DataSource;
};

export const deleteDataSource = async (id: number) => {
  await client.delete(`/datasources/${id}/`);
};

export const testConnection = async (id: number) => {
  const { data } = await client.post(`/datasources/${id}/test/`);
  return data as { success: boolean; message: string };
};

export const syncDataSource = async (id: number) => {
  const { data } = await client.post(`/datasources/${id}/sync/`);
  return data as { status: string; rows_imported?: number; error_message?: string };
};

export const fetchSyncLogs = async (id: number) => {
  const { data } = await client.get(`/datasources/${id}/logs/`);
  return data as SyncLog[];
};

export const fetchRecords = async (id: number) => {
  const { data } = await client.get(`/datasources/${id}/records/`);
  return data as { columns: string[]; rows: Record<string, unknown>[]; row_count: number };
};
