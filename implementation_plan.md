# Implementation Plan: BI Panel Feature Gap Analysis & Enhancement

## Overview

بررسی کامل پروژه Sana و شناسایی امکاناتی که برای داشتن یک پنل BI حرفه‌ای کم دارد. پروژه فعلی زیرساخت پایه‌ای خوبی دارد (Django REST + React + Recharts) اما برای رقابت با ابزارهایی مانند Metabase, Grafana, Power BI نیاز به امکانات کلیدی دارد.

## Current State Analysis

### What Exists:
- CRUD کامل برای Charts, Dashboards, Datasets, Saved Queries
- ۶ نوع نمودار (bar, line, pie, scatter, area, heatmap)
- Dashboard با قابلیت drag-and-drop (react-grid-layout)
- SQL Editor سفارشی
- JWT Authentication
- Pagination, Filtering, Sorting در API

### What's Missing (Gap Analysis):

---

## Types

### New Type Definitions Needed:

```typescript
// 1. KPI / Scorecard Widget
interface KPIWidget {
  id: number;
  name: string;
  dataset: number;
  metric: string;           // column name to aggregate
  aggregation: 'sum' | 'avg' | 'count' | 'min' | 'max';
  filters: Filter[];
  format: 'number' | 'currency' | 'percentage';
  comparison?: {
    type: 'previous_period' | 'previous_year' | 'static';
    value?: number;
  };
  thresholds?: {
    warning: number;
    critical: number;
  };
}

// 2. Dashboard Global Filters
interface DashboardFilter {
  id: string;
  name: string;
  type: 'date_range' | 'dropdown' | 'text_input' | 'number_range';
  column: string;
  dataset: number;
  defaultValue?: unknown;
  options?: { label: string; value: string }[];
}

// 3. Chart Export Config
interface ExportConfig {
  format: 'png' | 'svg' | 'pdf' | 'csv' | 'xlsx';
  width?: number;
  height?: number;
  filename?: string;
}

// 4. Alert/Notification
interface DataAlert {
  id: number;
  name: string;
  dataset: number;
  metric: string;
  aggregation: string;
  condition: 'above' | 'below' | 'equals' | 'change_percent';
  threshold: number;
  check_interval: 'hourly' | 'daily' | 'weekly';
  notification_channels: ('email' | 'webhook')[];
  recipients: number[];
  is_active: boolean;
  last_checked: string;
  last_triggered: string;
}

// 5. Scheduled Report
interface ScheduledReport {
  id: number;
  name: string;
  dashboard: number;
  format: 'pdf' | 'email_html';
  schedule: {
    frequency: 'daily' | 'weekly' | 'monthly';
    day_of_week?: number;
    day_of_month?: number;
    time: string;
    timezone: string;
  };
  recipients: number[];
  is_active: boolean;
}

// 6. Drill-down Config
interface DrillDownConfig {
  enabled: boolean;
  target_chart_id?: number;
  target_dashboard_id?: number;
  drill_column?: string;
  pass_filters?: boolean;
}

// 7. Chart Annotation
interface ChartAnnotation {
  id: number;
  chart: number;
  text: string;
  x_value?: string;
  y_value?: number;
  color: string;
  created_by: number;
}

// 8. Dashboard Template
interface DashboardTemplate {
  id: number;
  name: string;
  description: string;
  category: 'sales' | 'marketing' | 'finance' | 'operations' | 'custom';
  layout: DashboardLayout;
  chart_configs: Partial<ChartConfig>[];
  preview_image?: string;
}

// 9. Data Source Connector
interface DataSource {
  id: number;
  name: string;
  type: 'postgresql' | 'mysql' | 'sqlite' | 'api' | 'csv';
  connection_config: Record<string, unknown>;
  sync_schedule?: string;
  last_synced: string;
  status: 'active' | 'error' | 'syncing';
}

// 10. User Permissions
interface DashboardPermission {
  dashboard: number;
  user: number;
  permission: 'view' | 'edit' | 'admin';
  shared_at: string;
}
```

## Files

### New Backend Files:
- `backend/alerts/` - New Django app for data alerts
- `backend/alerts/models.py` - DataAlert, AlertHistory models
- `backend/alerts/views.py` - CRUD + check triggers
- `backend/alerts/serializers.py`
- `backend/alerts/tasks.py` - Celery periodic task for alert checks
- `backend/reports/` - New Django app for scheduled reports
- `backend/reports/models.py` - ScheduledReport model
- `backend/reports/views.py`
- `backend/reports/tasks.py` - Celery beat schedule
- `backend/datasources/` - New Django app for external data sources
- `backend/datasources/models.py` - DataSource, SyncLog models
- `backend/datasources/connectors.py` - DB connector implementations
- `backend/exports/` - Export utilities (PNG, PDF, CSV generation)
- `backend/exports/services.py` - Export service layer

### New Frontend Files:
- `frontend/src/components/charts/KPIWidget.tsx` - KPI scorecard component
- `frontend/src/components/charts/ChartExportButton.tsx` - Export dropdown
- `frontend/src/components/charts/DrillDownHandler.tsx` - Drill-down wrapper
- `frontend/src/components/charts/ChartAnnotations.tsx` - Annotation overlay
- `frontend/src/components/dashboard/DashboardFilters.tsx` - Global filter bar
- `frontend/src/components/dashboard/ShareDialog.tsx` - Permission sharing UI
- `frontend/src/components/dashboard/ScheduledReports.tsx` - Report scheduling UI
- `frontend/src/components/alerts/AlertList.tsx` - Alert management page
- `frontend/src/components/alerts/AlertConfigDialog.tsx` - Alert creation form
- `frontend/src/pages/TemplatesPage.tsx` - Dashboard templates gallery
- `frontend/src/pages/DataSourcesPage.tsx` - Data source management

### Existing Files to Modify:
- `backend/charts/models.py` - Add annotations, drill-down config to Chart
- `backend/dashboards/models.py` - Add filters, permissions, sharing fields
- `backend/dashboards/views.py` - Add permission checks, filter endpoints
- `backend/dashboards/serializers.py` - Include filters, permissions
- `backend/config/settings/base.py` - Add new apps to INSTALLED_APPS
- `backend/config/urls.py` - Register new app URLs
- `frontend/src/types.ts` - Add all new type definitions
- `frontend/src/pages/DashboardView.tsx` - Add filters bar, export, KPI widgets
- `frontend/src/components/charts/` - Add new chart types (gauge, funnel, treemap)
- `frontend/src/pages/ChartBuilder.tsx` - Add drill-down and annotation config
- `backend/requirements.txt` - Add celery-beat, weasyprint/pdfkit, psycopg2

## Functions

### New Backend Functions:
- `alerts/services.py::check_alert(alert_id)` - Evaluate alert condition against data
- `alerts/services.py::send_alert_notification(alert, trigger_data)` - Dispatch notifications
- `reports/services.py::generate_report(report_id)` - Render dashboard to PDF/HTML
- `reports/services.py::send_report(report, file_path)` - Email report to recipients
- `datasources/connectors.py::test_connection(config)` - Validate data source connectivity
- `datasources/connectors.py::sync_data(source_id)` - Pull data from external source
- `exports/services.py::export_chart(chart_id, format)` - Render chart to file
- `exports/services.py::export_dashboard(dashboard_id, format)` - Render full dashboard
- `dashboards/views.py::DashboardFilterViewSet` - CRUD for dashboard filters
- `dashboards/views.py::DashboardPermissionViewSet` - Share/unshare dashboard
- `charts/views.py::ChartDataExportView` - Export chart underlying data

### New Frontend Functions:
- `hooks/useAutoRefresh.ts` - Hook for periodic data refresh
- `hooks/useDashboardFilters.ts` - Hook for global filter state management
- `utils/exportChart.ts` - Client-side chart-to-image conversion
- `utils/formatNumber.ts` - KPI number formatting (currency, percentage)

## Classes

### New Backend Classes:
- `alerts/models.py::DataAlert` - Alert definition with conditions
- `alerts/models.py::AlertHistory` - Log of triggered alerts
- `reports/models.py::ScheduledReport` - Report schedule config
- `datasources/models.py::DataSource` - External data source connection
- `datasources/models.py::SyncLog` - Data sync history
- `datasources/connectors.py::PostgreSQLConnector` - PostgreSQL connector
- `datasources/connectors.py::MySQLConnector` - MySQL connector
- `datasources/connectors.py::APISourceConnector` - REST API connector

### Modified Backend Classes:
- `charts/models.py::Chart` - Add `annotations` relation, `drill_down_config` JSONField
- `dashboards/models.py::Dashboard` - Add `filters` JSONField, `is_public` BooleanField
- `dashboards/models.py::DashboardPermission` - New model for sharing

### New Frontend Classes/Components:
- `KPIWidget.tsx` - Scorecard with comparison and thresholds
- `GaugeChart.tsx` - Gauge/dial chart type
- `FunnelChart.tsx` - Funnel conversion chart
- `TreemapChart.tsx` - Hierarchical treemap
- `RadarChart.tsx` - Spider/radar chart
- `ChartTooltip.tsx` - Enhanced tooltip with actions

## Dependencies

### New Backend Packages:
- `celery[redis]` - Already likely installed, verify for background tasks
- `django-celery-beat` - Periodic task scheduling for alerts/reports
- `weasyprint` or `pdfkit` - PDF generation for scheduled reports
- `matplotlib` - Server-side chart rendering for PNG/PDF export
- `psycopg2-binary` - PostgreSQL connector (if not already present)
- `pymysql` - MySQL connector
- `requests` - For API data source connector

### New Frontend Packages:
- `html2canvas` or `dom-to-image` - Client-side chart export to PNG
- `file-saver` - Download files from browser
- `date-fns` - Date range filtering utilities
- `react-select` - Enhanced dropdown for filters

## Testing

- Unit tests for alert condition evaluation logic
- Integration tests for data source sync
- E2E tests for dashboard filter propagation to charts
- API tests for permission checks on shared dashboards
- Frontend component tests for KPIWidget, export functionality

## Implementation Order

1. **Dashboard Global Filters** (backend + frontend) - Highest impact, immediate UX improvement
2. **KPI/Scorecard Widget** - Most requested BI feature, new chart type
3. **Chart Export (PNG/CSV)** - Quick win, client-side first
4. **New Chart Types** (gauge, funnel, treemap, radar) - Expand visualization options
5. **Data Alerts System** - Background monitoring with notifications
6. **Dashboard Sharing & Permissions** - Multi-user collaboration
7. **Scheduled Reports** - Automated PDF/email reports
8. **External Data Source Connectors** - PostgreSQL, MySQL, API sources
9. **Drill-down Capability** - Interactive chart exploration
10. **Dashboard Templates** - Pre-built industry dashboards
11. **Chart Annotations** - Collaborative notes on charts
12. **Auto-refresh** - Real-time data updates

---

## Summary of Critical Gaps (پرکاربردترین امکانات کم‌دیده‌شده):

| اولویت | امکان | اهمیت |
|--------|-------|-------|
| 1 | فیلترهای سراسری داشبورد (Global Filters) | 🔴 بحرانی |
| 2 | ویجت KPI / Scorecard | 🔴 بحرانی |
| 3 | خروجی نمودار (PNG/CSV/PDF) | 🟡 مهم |
| 4 | انواع نمودار جدید (Gauge, Funnel, Treemap) | 🟡 مهم |
| 5 | سیستم هشدار داده (Alerts) | 🟡 مهم |
| 6 | اشتراک‌گذاری و سطوح دسترسی | 🟡 مهم |
| 7 | گزارش‌های زمان‌بندی شده | 🟢 مفید |
| 8 | اتصال به منابع داده خارجی | 🟢 مفید |
| 9 | Drill-down تعاملی | 🟢 مفید |
| 10 | قالب‌های آماده داشبورد | 🟢 مفید |