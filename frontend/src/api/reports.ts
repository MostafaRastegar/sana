import client from "./client";
import type { ScheduledReport } from "../types";

export const fetchReports = async (params?: Record<string, unknown>) => {
  const { data } = await client.get("/reports/", { params });
  return data as { count: number; results: ScheduledReport[] };
};

export const fetchReportById = async (id: number) => {
  const { data } = await client.get(`/reports/${id}/`);
  return data as ScheduledReport;
};

export const createReport = async (report: Partial<ScheduledReport>) => {
  const { data } = await client.post("/reports/", report);
  return data as ScheduledReport;
};

export const updateReport = async (id: number, report: Partial<ScheduledReport>) => {
  const { data } = await client.put(`/reports/${id}/`, report);
  return data as ScheduledReport;
};

export const deleteReport = async (id: number) => {
  await client.delete(`/reports/${id}/`);
};

export const triggerNow = async (id: number) => {
  const { data } = await client.post(`/reports/${id}/trigger_now/`);
  return data as { status: string; message: string };
};

export const toggleReport = async (id: number) => {
  const { data } = await client.post(`/reports/${id}/toggle/`);
  return data as ScheduledReport;
};

export const fetchReportHistory = async (id: number) => {
  const { data } = await client.get(`/reports/${id}/history/`);
  return data as import("../types").ReportHistory[];
};

export const previewReport = async (id: number) => {
  const { data } = await client.get(`/reports/${id}/preview/`, { responseType: "text" });
  return data as string;
};

export const downloadReport = async (id: number) => {
  const response = await client.get(`/reports/${id}/download/`, { responseType: "blob" });
  return response;
};
