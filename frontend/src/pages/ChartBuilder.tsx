import { useEffect, useState, useCallback } from "react";
import { Select, Button, Spin, Alert, Card, Input, message } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { useChartStore } from "../store/chartStore";
import { useDatasetStore } from "../store/datasetStore";
import EChartRenderer from "../components/charts/EChartRenderer";
import ChartTypeSelector from "../components/charts/ChartTypeSelector";
import ColumnMapper from "../components/charts/ColumnMapper";
import FilterBuilder from "../components/charts/FilterBuilder";
import { buildEChartsOption } from "../utils/chartOptions";
import { previewChartData } from "../api/charts";
import type { ChartType, ChartConfig, Column, Filter } from "../types";

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
  const [chartData, setChartData] = useState<Record<string, unknown> | null>(null);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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
    if (!selectedDataset || !xAxis || !yAxis) return;
    setDataLoading(true);
    setDataError(null);
    try {
      const agg = aggregate === "none" ? undefined : aggregate;
      const config: ChartConfig = {
        xAxis, yAxis, groupBy,
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
        <div className="space-y-4">
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
          {selectedDataset && xAxis && yAxis && (
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
            ) : (
              <EChartRenderer option={option as Record<string, unknown>} height={350} />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
