import { useEffect, useState, useCallback } from "react";
import { Select, Button, Spin, Alert, Card, Input, InputNumber, message } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { useChartStore } from "../store/chartStore";
import { useDatasetStore } from "../store/datasetStore";
import EChartRenderer from "../components/charts/EChartRenderer";
import KPIWidget from "../components/charts/KPIWidget";
import ChartTypeSelector from "../components/charts/ChartTypeSelector";
import ColumnMapper from "../components/charts/ColumnMapper";
import FilterBuilder from "../components/charts/FilterBuilder";
import { buildEChartsOption } from "../utils/chartOptions";
import { previewChartData } from "../api/charts";
import type { ChartType, ChartConfig, Column, Filter, KPIChartConfig, DrillDownConfig } from "../types";

const AGGREGATE_REQUIRED: ChartType[] = ["pie"];
const AGGREGATE_DISABLED: ChartType[] = ["scatter", "heatmap"];

export default function ChartBuilder() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentChart, loading, error, fetchChartById, createChart, updateChart } = useChartStore();
  const { datasets, fetchDatasets } = useDatasetStore();

  const [chartType, setChartType] = useState<ChartType>("bar");
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [columns, setColumns] = useState<Column[]>([]);
  const [xAxis, setXAxis] = useState<string>("");
  const [yAxis, setYAxis] = useState<string>("");
  const [groupBy, setGroupBy] = useState<string | undefined>();
  const [aggregate, setAggregate] = useState<string>("none");
  const [filters, setFilters] = useState<Filter[]>([]);
  const [drillDownConfig, setDrillDownConfig] = useState<DrillDownConfig>({ enabled: false });
  const [chartData, setChartData] = useState<Record<string, unknown> | null>(null);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { charts } = useChartStore();

  const isEditing = !!id;
  const selectedDatasetObj = datasets.find((d) => d.id === selectedDataset);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  useEffect(() => {
    if (id) {
      fetchChartById(parseInt(id));
    }
  }, [id, fetchChartById]);

  useEffect(() => {
    if (isEditing && currentChart) {
      setChartType(currentChart.chart_type);
      setSelectedDataset(currentChart.dataset);
      setXAxis(currentChart.config.xAxis);
      setYAxis(currentChart.config.yAxis);
      setGroupBy(currentChart.config.groupBy);
      setAggregate(currentChart.config.aggregate || "none");
      setFilters(currentChart.config.filters || []);
      setDrillDownConfig(currentChart.drill_down_config || { enabled: false });
    }
  }, [isEditing, currentChart]);

  useEffect(() => {
    if (selectedDatasetObj) {
      setColumns(selectedDatasetObj.columns);
    } else {
      setColumns([]);
    }
  }, [selectedDatasetObj]);

  const handleChartTypeChange = (newType: ChartType) => {
    setChartType(newType);
    setChartData(null);
    if (AGGREGATE_REQUIRED.includes(newType) && aggregate === "none") {
      setAggregate("sum");
    } else if (AGGREGATE_DISABLED.includes(newType)) {
      setAggregate("none");
      setGroupBy(undefined);
    }
  };

  const fetchPreview = useCallback(async () => {
    if (!selectedDataset) return;
    const isKpi = chartType === "kpi";
    if (!isKpi && (!xAxis || !yAxis)) return;
    if (isKpi && !yAxis) return;
    setDataLoading(true);
    setDataError(null);
    try {
      const agg = aggregate === "none" ? undefined : aggregate;
      const config: ChartConfig = {
        xAxis: isKpi ? "" : xAxis,
        yAxis, groupBy,
        aggregate: agg as ChartConfig["aggregate"],
        filters: filters.filter((f) => f.column),
      };
      const data = await previewChartData(selectedDataset, { ...config }, chartType);
      setChartData(data as unknown as Record<string, unknown>);
    } catch (err) {
      setDataError((err as Error).message);
    } finally {
      setDataLoading(false);
    }
  }, [selectedDataset, xAxis, yAxis, groupBy, aggregate, filters, id, chartType]);

  useEffect(() => {
    if (isEditing && selectedDataset && xAxis && yAxis) {
      fetchPreview();
    }
  }, [isEditing, selectedDataset, xAxis, yAxis, groupBy, aggregate, filters, chartType, fetchPreview]);

  const handleSave = async () => {
    if (!selectedDataset) {
      message.error("Please select a dataset");
      return;
    }
    setSaving(true);
    try {
      const agg = aggregate === "none" ? undefined : aggregate;
      const chartConfig: ChartConfig = {
        xAxis, yAxis, groupBy,
        aggregate: agg as ChartConfig["aggregate"],
        filters: filters.filter((f) => f.column),
      };
      const payload: Partial<import("../types").Chart> = {
        name: (document.getElementById("chart-name") as HTMLInputElement)?.value || "Untitled Chart",
        description: (document.getElementById("chart-desc") as HTMLTextAreaElement)?.value || "",
        dataset: selectedDataset,
        chart_type: chartType,
        config: chartConfig,
        drill_down_config: drillDownConfig.enabled ? drillDownConfig : null,
      };
      if (isEditing && id) {
        await updateChart(parseInt(id), payload);
        message.success("Chart updated");
      } else {
        const created = await createChart(payload);
        if (created) {
          message.success("Chart created");
          navigate(`/charts/${created.id}`);
        }
      }
    } catch {
      message.error("Failed to save chart");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (error) return <Alert type="error" message={error} className="m-4" />;

  const option = chartData ? buildEChartsOption(chartType, chartData as unknown as import("../types").ChartData) : {};

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">
          {isEditing ? `Edit: ${currentChart?.name || ""}` : "New Chart"}
        </h2>
        <Button type="primary" onClick={handleSave} loading={saving}>
          {isEditing ? "Update" : "Save"} Chart
        </Button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="flex flex-col gap-4">
          <Card title="Basic Info">
            <input
              id="chart-name"
              type="text"
              defaultValue={currentChart?.name || ""}
              placeholder="Chart name"
              className="w-full px-3 py-2 border rounded mb-3"
            />
            <textarea
              id="chart-desc"
              defaultValue={currentChart?.description || ""}
              placeholder="Description (optional)"
              rows={2}
              className="w-full px-3 py-2 border rounded"
            />
          </Card>
          <Card title="Dataset">
            <Select
              value={selectedDataset}
              onChange={(val) => { setSelectedDataset(val); setChartData(null); }}
              placeholder="Select a dataset"
              className="w-full"
              options={datasets.map((d) => ({ value: d.id, label: d.name }))}
            />
          </Card>
          <Card title="Chart Type">
            <ChartTypeSelector value={chartType} onChange={handleChartTypeChange} />
          </Card>
          {chartType === "kpi" && (
            <Card title="KPI Configuration">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Metric Column</label>
                  <Select
                    value={yAxis || undefined}
                    onChange={(v) => { setYAxis(v); setChartData(null); }}
                    placeholder="Select metric column"
                    className="w-full"
                    options={columns.map((c: Column) => ({ value: c.name, label: c.name }))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Aggregation</label>
                  <Select
                    value={aggregate}
                    onChange={(v) => setAggregate(v)}
                    className="w-full"
                    options={[
                      { value: "sum", label: "Sum" },
                      { value: "avg", label: "Average" },
                      { value: "count", label: "Count" },
                      { value: "min", label: "Minimum" },
                      { value: "max", label: "Maximum" },
                    ]}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Format</label>
                  <Select
                    value={(currentChart?.config as ChartConfig)?.kpi_format || "number"}
                    onChange={(v) => {
                      const cfg = (currentChart?.config as ChartConfig) || {};
                      cfg.kpi_format = v as "number" | "currency" | "percentage";
                      setChartData(null);
                    }}
                    className="w-full"
                    options={[
                      { value: "number", label: "Number" },
                      { value: "currency", label: "Currency ($)" },
                      { value: "percentage", label: "Percentage (%)" },
                    ]}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Comparison</label>
                  <Select
                    value={(currentChart?.config as ChartConfig)?.kpi_comparison?.type || "none"}
                    onChange={(v) => {
                      const cfg = (currentChart?.config as ChartConfig) || {};
                      if (v === "none") {
                        delete cfg.kpi_comparison;
                      } else {
                        cfg.kpi_comparison = { type: v as "previous_period" | "previous_year" | "static", value: 0 };
                      }
                      setChartData(null);
                    }}
                    className="w-full"
                    options={[
                      { value: "none", label: "No comparison" },
                      { value: "previous_period", label: "Previous period" },
                      { value: "previous_year", label: "Previous year" },
                      { value: "static", label: "Static target" },
                    ]}
                  />
                  {(currentChart?.config as ChartConfig)?.kpi_comparison?.type === "static" && (
                    <div className="mt-2">
                      <label className="block text-sm font-medium text-gray-600 mb-1">Target Value</label>
                      <Input
                        type="number"
                        defaultValue={(currentChart?.config as ChartConfig)?.kpi_comparison?.value || 0}
                        onChange={(e) => {
                          const cfg = (currentChart?.config as ChartConfig) || {};
                          if (!cfg.kpi_comparison) cfg.kpi_comparison = { type: "static", value: 0 };
                          cfg.kpi_comparison.value = parseFloat(e.target.value);
                        }}
                        placeholder="Target value"
                      />
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Thresholds</label>
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      type="number"
                      defaultValue={(currentChart?.config as ChartConfig)?.kpi_thresholds?.warning}
                      placeholder="Warning threshold"
                      onChange={(e) => {
                        const cfg = (currentChart?.config as ChartConfig) || {};
                        if (!cfg.kpi_thresholds) cfg.kpi_thresholds = { warning: 0, critical: 0 };
                        cfg.kpi_thresholds.warning = parseFloat(e.target.value);
                      }}
                    />
                    <Input
                      type="number"
                      defaultValue={(currentChart?.config as ChartConfig)?.kpi_thresholds?.critical}
                      placeholder="Critical threshold"
                      onChange={(e) => {
                        const cfg = (currentChart?.config as ChartConfig) || {};
                        if (!cfg.kpi_thresholds) cfg.kpi_thresholds = { warning: 0, critical: 0 };
                        cfg.kpi_thresholds.critical = parseFloat(e.target.value);
                      }}
                    />
                  </div>
                </div>
              </div>
            </Card>
          )}
          {columns.length > 0 && (
            <Card title="Column Mapping">
              <ColumnMapper
                columns={columns}
                chartType={chartType}
                xAxis={xAxis}
                yAxis={yAxis}
                groupBy={groupBy}
                aggregate={aggregate}
                onXAxisChange={(v) => { setXAxis(v); setChartData(null); }}
                onYAxisChange={(v) => { setYAxis(v); setChartData(null); }}
                onGroupByChange={(v) => { setGroupBy(v); setChartData(null); }}
                onAggregateChange={(v) => { setAggregate(v); setChartData(null); }}
              />
            </Card>
          )}
          {columns.length > 0 && (
            <Card title="Filters">
              <FilterBuilder
                columns={columns}
                filters={filters}
                onChange={setFilters}
              />
            </Card>
          )}
          <Card title="Drill-Down Configuration">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="drill-enabled"
                  checked={drillDownConfig.enabled}
                  onChange={(e) => setDrillDownConfig((p) => ({ ...p, enabled: e.target.checked }))}
                  className="w-4 h-4"
                />
                <label htmlFor="drill-enabled" className="text-sm font-medium">Enable Drill-Down</label>
              </div>
              {drillDownConfig.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">Drill Column</label>
                    <Select
                      value={drillDownConfig.drill_column || undefined}
                      onChange={(v) => setDrillDownConfig((p) => ({ ...p, drill_column: v }))}
                      placeholder="Select column (default: series name)"
                      className="w-full"
                      allowClear
                      options={columns.map((c: Column) => ({ value: c.name, label: c.name }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">Target Chart</label>
                    <Select
                      value={drillDownConfig.target_chart ?? undefined}
                      onChange={(v) => setDrillDownConfig((p) => ({ ...p, target_chart: v ?? null }))}
                      placeholder="Optional: navigate to this chart"
                      className="w-full"
                      allowClear
                      options={charts.map((c) => ({ value: c.id, label: c.name }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">Target Dashboard</label>
                    <Select
                      value={drillDownConfig.target_dashboard ?? undefined}
                      onChange={(v) => setDrillDownConfig((p) => ({ ...p, target_dashboard: v ?? null }))}
                      placeholder="Optional: navigate to this dashboard"
                      className="w-full"
                      allowClear
                      options={[]}
                      disabled
                    />
                    <p className="text-xs text-gray-400 mt-1">Dashboard list (coming soon)</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="drill-pass-filters"
                      checked={drillDownConfig.pass_filters ?? false}
                      onChange={(e) => setDrillDownConfig((p) => ({ ...p, pass_filters: e.target.checked }))}
                      className="w-4 h-4"
                    />
                    <label htmlFor="drill-pass-filters" className="text-sm font-medium">Pass Global Filters</label>
                  </div>
                </>
              )}
            </div>
          </Card>
          {(chartType === "kpi" ? selectedDataset && yAxis : selectedDataset && xAxis && yAxis) && (
            <Button
              type="default"
              onClick={fetchPreview}
              loading={dataLoading}
              className="w-full"
            >
              Fetch Preview Data
            </Button>
          )}
        </div>
        <div>
          <Card title="Preview">
            {dataLoading ? (
              <div className="h-80 flex items-center justify-center">
                <Spin size="large" />
              </div>
            ) : dataError ? (
              <Alert type="error" message={dataError} />
            ) : !chartData ? (
              <div className="h-80 flex items-center justify-center text-gray-400">
                <p>Configure your chart and click "Fetch Preview Data"</p>
              </div>
            ) : chartType === "kpi" && chartData ? (
              <div className="h-80 flex items-center justify-center">
                <KPIWidget
                  label={(chartData as any)?.rows?.[0] ? "KPI" : "No Data"}
                  value={(chartData as any)?.rows?.[0]?.[Object.keys((chartData as any)?.rows?.[0] || {})[0]] ?? 0}
                  format={(currentChart?.config as ChartConfig)?.kpi_format || "number"}
                  thresholds={(currentChart?.config as ChartConfig)?.kpi_thresholds}
                />
              </div>
            ) : (
              <EChartRenderer option={option as Record<string, unknown>} height={350} />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
