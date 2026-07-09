export interface Column {
  name: string;
  type: string;
  label: string;
}

export interface Dataset {
  id: number;
  name: string;
  description: string;
  table_name: string;
  columns: Column[];
  row_count: number | null;
  column_count: number;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetData {
  columns: Column[];
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
}

export type ChartType =
  | "bar"
  | "line"
  | "pie"
  | "scatter"
  | "area"
  | "heatmap";

export interface Filter {
  column: string;
  operator: "eq" | "neq" | "gt" | "gte" | "lt" | "lte" | "in" | "contains";
  value: string | number | (string | number)[];
}

export interface ChartConfig {
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  filters?: Filter[];
  sort?: { column: string; direction: "asc" | "desc" };
  limit?: number;
  aggregate?: "sum" | "avg" | "count" | "min" | "max" | "none";
}

export interface Chart {
  id: number;
  name: string;
  description: string;
  dataset: number;
  dataset_name: string;
  chart_type: ChartType;
  chart_type_display: string;
  config: ChartConfig;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface ChartData {
  columns: Column[];
  rows: Record<string, unknown>[];
  chart_type: ChartType;
  config: ChartConfig;
}

export interface DashboardLayoutChart {
  chartId: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface DashboardFilter {
  id: string;
  name: string;
  type: "select" | "date" | "daterange" | "text" | "number";
  column: string;
  dataset: number | null;
  defaultValue: string | number | null;
  options?: string[];
  operator?: "eq" | "neq" | "gt" | "gte" | "lt" | "lte";
}

export interface DashboardLayout {
  charts: DashboardLayoutChart[];
}

export interface Dashboard {
  id: number;
  name: string;
  description: string;
  layout: DashboardLayout | null;
  filters: DashboardFilter[];
  chart_count: number;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface SavedQuery {
  id: number;
  name: string;
  sql: string;
  dataset: number | null;
  dataset_name: string | null;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface QueryResult {
  columns: Column[];
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
}