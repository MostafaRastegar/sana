import client from "./client";
import type { DataAlert, AlertHistory, AlertStats } from "../types";

export const fetchAlerts = async (params?: Record<string, unknown>) => {
  const { data } = await client.get("/alerts/", { params });
  return data as { count: number; results: DataAlert[] };
};

export const fetchAlertById = async (id: number) => {
  const { data } = await client.get(`/alerts/${id}/`);
  return data as DataAlert;
};

export const createAlert = async (alert: Partial<DataAlert>) => {
  const { data } = await client.post("/alerts/", alert);
  return data as DataAlert;
};

export const updateAlert = async (id: number, alert: Partial<DataAlert>) => {
  const { data } = await client.put(`/alerts/${id}/`, alert);
  return data as DataAlert;
};

export const deleteAlert = async (id: number) => {
  await client.delete(`/alerts/${id}/`);
};

export const toggleAlert = async (id: number) => {
  const { data } = await client.post(`/alerts/${id}/toggle/`);
  return data as DataAlert;
};

export const checkAlertNow = async (id: number) => {
  const { data } = await client.post(`/alerts/${id}/check_now/`);
  return data as { triggered: boolean; history?: AlertHistory; message?: string };
};

export const fetchAlertHistory = async (id: number, params?: Record<string, unknown>) => {
  const { data } = await client.get(`/alerts/${id}/history/`, { params });
  return data as { count: number; results: AlertHistory[] };
};

export const fetchAlertStats = async () => {
  const { data } = await client.get("/alerts/stats/");
  return data as AlertStats;
};