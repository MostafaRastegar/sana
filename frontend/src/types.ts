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
  | "heatmap"
  | "kpi"
  | "gauge"
  | "funnel"
  | "treemap"
  | "radar";

export interface Filter {
  column: string;
  operator: "eq" | "neq" | "gt" | "gte" | "lt" | "lte" | "in" | "contains";
  value: string | number | (string | number)[];
}

export interface KPIComparison {
  type: "previous_period" | "previous_year" | "static";
  value?: number;
}

export interface KPIThresholds {
  warning: number;
  critical: number;
  reversed?: boolean;
}

export interface KPIChartConfig {
  metric: string;
  aggregation: "sum" | "avg" | "count" | "min" | "max";
  format: "number" | "currency" | "percentage";
  comparison?: KPIComparison;
  thresholds?: KPIThresholds;
}

export interface ChartConfig {
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  filters?: Filter[];
  sort?: { column: string; direction: "asc" | "desc" };
  limit?: number;
  aggregate?: "sum" | "avg" | "count" | "min" | "max" | "none";
  // KPI-specific fields
  metric?: string;
  kpi_format?: "number" | "currency" | "percentage";
  kpi_comparison?: KPIComparison;
  kpi_thresholds?: KPIThresholds;
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

export type DashboardPermissionLevel = "view" | "edit" | "admin";

export interface Dashboard {
  id: number;
  name: string;
  description: string;
  layout: DashboardLayout | null;
  filters: DashboardFilter[];
  is_public: boolean;
  chart_count: number;
  shared_users_count: number;
  is_owner: boolean;
  user_permission: DashboardPermissionLevel | null;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardPermission {
  id: number;
  dashboard: number;
  user: number;
  user_name: string;
  permission: DashboardPermissionLevel;
  shared_by: number;
  created_at: string;
}

export interface UserSearchResult {
  id: number;
  username: string;
  email: string;
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

export type AlertCondition = "above" | "below" | "equals" | "change_percent";
export type AlertAggregation = "sum" | "avg" | "count" | "min" | "max";
export type AlertInterval = "hourly" | "daily" | "weekly" | "monthly";

export type SourceType = "postgresql" | "mysql" | "sqlite" | "api" | "csv";

export type DataSourceStatus = "active" | "error" | "syncing";

export interface DataSource {
  id: number;
  name: string;
  source_type: SourceType;
  source_type_display?: string;
  connection_config: Record<string, unknown>;
  sync_schedule: string;
  is_active: boolean;
  last_synced: string | null;
  status: DataSourceStatus;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export type SyncLogStatus = "running" | "success" | "failed";

export interface SyncLog {
  id: number;
  source: number;
  started_at: string;
  finished_at: string | null;
  status: SyncLogStatus;
  rows_imported: number;
  error_message: string;
  created_at: string;
}

export interface DataAlert {
  id: number;
  name: string;
  description: string;
  dataset: number;
  dataset_name: string;
  metric: string;
  aggregation: AlertAggregation;
  condition: AlertCondition;
  condition_display: string;
  threshold: number;
  check_interval: AlertInterval;
  notification_channels: string[];
  recipients: number[];
  recipient_ids: number[];
  webhook_url: string;
  filters: Record<string, unknown> | null;
  is_active: boolean;
  created_by: number;
  created_by_name: string;
  last_checked: string | null;
  last_triggered: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertHistory {
  id: number;
  alert: number;
  alert_name: string;
  triggered_at: string;
  actual_value: number;
  threshold: number;
  condition: string;
  message: string;
  notification_sent: boolean;
  notification_response: string;
}

export interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  triggered_last_24h: number;
}

export type ReportFrequency = "daily" | "weekly" | "monthly";
export type ReportFormat = "pdf" | "email_html";

export interface ReportRecipient {
  id: number;
  email: string;
}

export interface ReportHistory {
  id: number;
  report: number;
  sent_at: string;
  recipients_count: number;
  format: ReportFormat;
  status: "sent" | "failed";
  error_message?: string;
}

export interface ScheduledReport {
  id: number;
  name: string;
  description: string;
  dashboard: number;
  dashboard_name: string;
  format: ReportFormat;
  frequency: ReportFrequency;
  day_of_week: number | null;
  day_of_month: number | null;
  time: string;
  timezone: string;
  recipients: number[];
  recipients_count: number;
  is_active: boolean;
  last_sent: string | null;
  next_run: string | null;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  history: ReportHistory[];
}
