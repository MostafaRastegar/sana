import { useEffect, useState, useCallback, useRef } from "react";
import { Spin, Button, Modal, Select, message, Tag } from "antd";
import { EditOutlined, PlusOutlined, SaveOutlined, FilterOutlined, ShareAltOutlined } from "@ant-design/icons";
import { useDashboardStore } from "../store/dashboardStore";
import { useChartStore } from "../store/chartStore";
import { useParams, useNavigate } from "react-router-dom";
import GridLayout from "react-grid-layout";
import type { Layout, LayoutItem } from "react-grid-layout";
import EChartRenderer from "../components/charts/EChartRenderer";
import DrillDownBreadcrumb from "../components/charts/DrillDownBreadcrumb";
import KPIWidget from "../components/charts/KPIWidget";
import ChartExportButton from "../components/charts/ChartExportButton";
import { useDrillDown } from "../components/charts/DrillDownHandler";
import { buildEChartsOption } from "../utils/chartOptions";
import { fetchChartData } from "../api/charts";
import { DashboardFilters } from "../components/dashboard/DashboardFilters";
import { FilterManager } from "../components/dashboard/FilterManager";
import ShareModal from "../components/dashboard/ShareModal";
import type { Chart, ChartData, DashboardLayoutChart } from "../types";
import "react-grid-layout/css/styles.css";

interface ChartWithData {
  chart: Chart;
  data: ChartData | null;
  loading: boolean;
  drillData?: ChartData | null;
}

interface DrillStep {
  column: string;
  value: string;
  chartId: number;
  label: string;
}

function ChartDrillWrapper({
  chartId,
  chartInfo,
  dataWrapper,
  isEditing,
  canEdit,
  onRemove,
  onDrill,
  onDrillStep,
}: {
  chartId: number;
  chartInfo: Chart | undefined;
  dataWrapper: ChartWithData | undefined;
  isEditing: boolean;
  canEdit: boolean;
  onRemove: (id: string) => void;
  onDrill: (chartId: number, data: ChartData) => void;
  onDrillStep: (step: DrillStep) => void;
}) {
  const chartOption = dataWrapper?.data
    ? buildEChartsOption(dataWrapper.data.chart_type, dataWrapper.data)
    : {};

  const isKpi = chartInfo?.chart_type === "kpi";
  const kpiValue = isKpi && dataWrapper?.data?.rows?.[0]
    ? Object.values(dataWrapper.data.rows[0])[0] as number | string
    : null;
  const cfg = chartInfo?.config as Record<string, unknown> | undefined;
  const kpiConfig = {
    format: (cfg?.kpi_format as "number" | "currency" | "percentage") || "number",
    thresholds: cfg?.kpi_thresholds as { warning: number; critical: number; reversed?: boolean } | undefined,
    comparison: cfg?.kpi_comparison as { type: "previous_period" | "previous_year" | "static"; value?: number } | undefined,
  };

  const chartConfig = chartInfo?.config
    ? { xAxis: chartInfo.config.xAxis || "", yAxis: (chartInfo.config as any).yAxis || "" }
    : { xAxis: "", yAxis: "" };
  const { chartClickEvents } = useDrillDown({
    chartId,
    config: chartInfo?.drill_down_config ?? null,
    chartConfig,
    onDrill,
    onDrillStep,
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden h-full">
      <div className="flex justify-between items-center px-3 py-2 bg-gray-50 border-b">
        <span className="font-medium text-sm truncate">
          {chartInfo?.name || `Chart #${chartId}`}
        </span>
        <div className="flex items-center gap-1">
          <ChartExportButton
            chartId={chartId}
            chartName={chartInfo?.name || `Chart #${chartId}`}
          />
          {isEditing && canEdit && (
            <Button
              danger
              size="small"
              onClick={() => onRemove(String(chartId))}
            >
              Remove
            </Button>
          )}
        </div>
      </div>
      <div className="p-2 h-[calc(100%-40px)]" data-chart-id={chartId}>
        {dataWrapper?.loading ? (
          <div className="h-full flex items-center justify-center">
            <Spin />
          </div>
        ) : isKpi ? (
          <KPIWidget
            label={chartInfo?.name || `Chart #${chartId}`}
            value={kpiValue ?? 0}
            format={kpiConfig.format}
            thresholds={kpiConfig.thresholds}
            previous={kpiConfig.comparison?.type === "static" ? kpiConfig.comparison.value ?? null : null}
            loading={false}
            className="h-full"
          />
        ) : (
          <EChartRenderer
            option={chartOption as Record<string, unknown>}
            height="100%"
            onEvents={chartClickEvents}
          />
        )}
      </div>
    </div>
  );
}

export default function DashboardView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentDashboard, loading, error, fetchDashboardById, updateLayout } = useDashboardStore();
  const { charts, fetchCharts } = useChartStore();
  const [chartDataMap, setChartDataMap] = useState<Record<number, ChartWithData>>({});
  const [isEditing, setIsEditing] = useState(false);
  const [layout, setLayout] = useState<LayoutItem[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [width, setWidth] = useState(window.innerWidth);
  const [filterValues, setFilterValues] = useState<Record<string, string | number | null>>({});
  const filterValuesRef = useRef(filterValues);
  filterValuesRef.current = filterValues;
  const [filterManagerOpen, setFilterManagerOpen] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [drillStack, setDrillStack] = useState<DrillStep[]>([]);
  const [drillStepIndex, setDrillStepIndex] = useState<number>(-1);
  const chartRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const currentIdRef = useRef<string | undefined>(undefined);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (!id) return;
    const dashId = parseInt(id);
    currentIdRef.current = id;
    // Reset store + local state before fetch to prevent stale render
    useDashboardStore.setState({ currentDashboard: null, loading: true });
    setChartDataMap({});
    setLayout([]);
    setDrillStack([]);
    setDrillStepIndex(-1);
    setFilterValues({});
    fetchDashboardById(dashId);
    fetchCharts();
  }, [id, fetchDashboardById, fetchCharts]);

  useEffect(() => {
    if (!id) return;
    const dashId = parseInt(id);
    if (currentDashboard?.id !== dashId) return;
    let ignore = false;
    const savedCharts = currentDashboard?.layout?.charts;
    if (savedCharts && charts.length > 0) {
      setLayout((prev) => {
        if (prev.length > 0) return prev;
        return savedCharts.map((c: DashboardLayoutChart) => ({
          i: String(c.chartId),
          x: c.x,
          y: c.y,
          w: c.w,
          h: c.h,
        }));
      });

      const chartIds = savedCharts.map((c: DashboardLayoutChart) => c.chartId);
      chartIds.forEach((chartId: number) => {
        if (!chartDataMap[chartId]) {
          loadChartData(chartId);
        }
      });
    }
    return () => { ignore = true; };
  }, [currentDashboard, charts, id]);

  const loadChartData = async (chartId: number, globalFilters?: Record<string, unknown>[]) => {
    const idAtCall = currentIdRef.current;
    setChartDataMap((prev: Record<number, ChartWithData>) => ({ ...prev, [chartId]: { ...prev[chartId], loading: true } }));
    try {
      const params: Record<string, unknown> = {};
      if (globalFilters?.length) {
        params.global_filters = JSON.stringify(globalFilters);
      }
      const data = await fetchChartData(chartId, params);
      // Discard stale response if user navigated away
      if (currentIdRef.current !== idAtCall) return;
      const chart = charts.find((c: Chart) => c.id === chartId);
      if (chart) {
        setChartDataMap((prev: Record<number, ChartWithData>) => ({
          ...prev,
          [chartId]: { chart, data, loading: false },
        }));
      }
    } catch {
      if (currentIdRef.current !== idAtCall) return;
      setChartDataMap((prev: Record<number, ChartWithData>) => ({
        ...prev,
        [chartId]: { ...prev[chartId], loading: false },
      }));
    }
  };

  const reloadAllCharts = useCallback(() => {
    const savedCharts = currentDashboard?.layout?.charts;
    if (!savedCharts) return;
    const currentValues = filterValuesRef.current;
    const activeFilters = currentDashboard?.filters
      ?.filter((f) => currentValues[f.id] != null && currentValues[f.id] !== "")
      .map((f) => {
        const raw = currentValues[f.id];
        let value = raw;
        const validOps = ["eq", "neq", "gt", "gte", "lt", "lte"] as const;
        type Op = typeof validOps[number];
        let operator: Op = (f.operator as Op) || "eq";
        if (typeof raw === "string" && /^(eq|neq|gt|gte|lt|lte):/.test(raw)) {
          const parts = raw.split(":");
          operator = (validOps.includes(parts[0] as Op) ? parts[0] : "eq") as Op;
          value = parts.slice(1).join(":");
        }
        return { column: f.column, value, operator };
      }) || [];
    savedCharts.forEach((sc: DashboardLayoutChart) => {
      loadChartData(sc.chartId, activeFilters.length ? activeFilters : undefined);
    });
  }, [currentDashboard]);

  const handleFilterChange = (filterId: string, value: string | number | null) => {
    setFilterValues((prev) => ({ ...prev, [filterId]: value }));
  };

  const handleClearFilters = () => {
    setFilterValues({});
  };

  useEffect(() => {
    if (!currentDashboard?.layout?.charts?.length) return;
    reloadAllCharts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterValues]);

  const handleLayoutChange = useCallback((newLayout: Layout) => {
    if (isEditing) {
      setLayout([...newLayout]);
    }
  }, [isEditing]);

  const handleSaveLayout = async () => {
    if (!id) return;
    setSaving(true);
    const dashboardLayout = {
      charts: layout.map((item: LayoutItem) => ({
        chartId: parseInt(item.i),
        x: item.x,
        y: item.y,
        w: item.w,
        h: item.h,
      })),
    };
    await updateLayout(parseInt(id), dashboardLayout);
    setSaving(false);
    setIsEditing(false);
    message.success("Layout saved");
  };

  const handleAddChart = (chartId: number) => {
    const maxY = layout.reduce((max: number, item: LayoutItem) => Math.max(max, item.y + item.h), 0);
    setLayout([
      ...layout,
      { i: String(chartId), x: 0, y: maxY, w: 6, h: 4 },
    ]);
    loadChartData(chartId);
    setAddModalOpen(false);
  };

  const handleRemoveChart = (chartId: string) => {
    setLayout(layout.filter((item: LayoutItem) => item.i !== chartId));
  };

  const handleDrill = (chartId: number, data: ChartData) => {
    setChartDataMap((prev: Record<number, ChartWithData>) => ({
      ...prev,
      [chartId]: {
        ...prev[chartId],
        data: data as any,
        drillData: data,
      },
    }));
  };

  const handleDrillStep = (step: DrillStep) => {
    setDrillStack((prev) => [...prev, step]);
    setDrillStepIndex((prev) => prev + 1);
  };

  const handleNavigateUp = (index: number) => {
    const newStack = drillStack.slice(0, index);
    setDrillStack(newStack);
    setDrillStepIndex(index - 1);
    // Reload original chart data for all affected charts
    const affectedCharts = layout.map((l: LayoutItem) => parseInt(l.i));
    affectedCharts.forEach((cid: number) => {
      const wrapper = chartDataMap[cid];
      if (wrapper?.drillData) {
        // Revert to original; reload if needed
        loadChartData(cid);
      }
    });
  };

  const handleDrillReset = () => {
    setDrillStack([]);
    setDrillStepIndex(-1);
    const affectedCharts = layout.map((l: LayoutItem) => parseInt(l.i));
    affectedCharts.forEach((cid: number) => {
      loadChartData(cid);
    });
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (!currentDashboard) return <Spin className="block mx-auto mt-8" />;

  const canEdit = currentDashboard.user_permission === "admin" ||
    currentDashboard.user_permission === "edit" ||
    currentDashboard.is_owner;
  const addedChartIds = layout.map((l: LayoutItem) => parseInt(l.i));
  const availableCharts = charts.filter((c: Chart) => !addedChartIds.includes(c.id));

  return (
    <div key={id}>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold">{currentDashboard.name}</h2>
          {currentDashboard.description && (
            <p className="text-gray-500">{currentDashboard.description}</p>
          )}
          {currentDashboard.user_permission && (
            <Tag color={currentDashboard.user_permission === "admin" ? "red" : currentDashboard.user_permission === "edit" ? "blue" : "green"}>
              {currentDashboard.user_permission.toUpperCase()}
            </Tag>
          )}
        </div>
        <div className="space-x-2">
          {canEdit && (
            <>
              <Button icon={<ShareAltOutlined />} onClick={() => setShareModalOpen(true)}>
                Share
              </Button>
              <Button icon={<FilterOutlined />} onClick={() => setFilterManagerOpen(true)}>
                Manage Filters
              </Button>
            </>
          )}
          {canEdit && !isEditing ? (
            <Button icon={<EditOutlined />} onClick={() => setIsEditing(true)}>
              Edit Layout
            </Button>
          ) : canEdit && isEditing ? (
            <>
              <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
                Add Chart
              </Button>
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveLayout} loading={saving}>
                Save Layout
              </Button>
              <Button onClick={() => setIsEditing(false)}>Cancel</Button>
            </>
          ) : null}
        </div>
      </div>

      <DashboardFilters
        filters={currentDashboard.filters || []}
        values={filterValues}
        onChange={handleFilterChange}
        onClear={handleClearFilters}
      />

      {layout.length === 0 ? (
        <div className="bg-gray-50 h-96 flex items-center justify-center rounded-lg border-2 border-dashed">
          <div className="text-center">
            <p className="text-gray-400 mb-2">No charts in this dashboard</p>
            {canEdit && (
              <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
                Add Chart
              </Button>
            )}
          </div>
        </div>
      ) : (
        <>
          {drillStack.length > 0 && (
            <DrillDownBreadcrumb
              steps={drillStack}
              onNavigateUp={handleNavigateUp}
              onReset={handleDrillReset}
            />
          )}
          <div style={{ width: "100%", position: "relative", left: "50%", transform: "translateX(-50%)" }}>
            <GridLayout
              layout={layout}
              width={width}
              autoSize
              onLayoutChange={handleLayoutChange}
              gridConfig={{ cols: 12, rowHeight: 100, margin: [10, 10] }}
              dragConfig={{ enabled: isEditing }}
              resizeConfig={{ enabled: isEditing }}
            >
              {layout.map((item: LayoutItem) => {
                const chartId = parseInt(item.i);
                const chartInfo = charts.find((c: Chart) => c.id === chartId);
                const dataWrapper = chartDataMap[chartId];
                return (
                  <div key={item.i}>
                    <ChartDrillWrapper
                      chartId={chartId}
                      chartInfo={chartInfo}
                      dataWrapper={dataWrapper}
                      isEditing={isEditing}
                      canEdit={canEdit}
                      onRemove={handleRemoveChart}
                      onDrill={handleDrill}
                      onDrillStep={handleDrillStep}
                    />
                  </div>
                );
              })}
            </GridLayout>
          </div>
        </>
      )}

      <Modal
        title="Add Chart"
        open={addModalOpen}
        onCancel={() => setAddModalOpen(false)}
        footer={null}
      >
        {availableCharts.length === 0 ? (
          <p className="text-gray-400">All charts are already added. Create new charts first.</p>
        ) : (
          <Select
            className="w-full"
            placeholder="Select a chart to add"
            onSelect={handleAddChart}
            options={availableCharts.map((c: Chart) => ({
              value: c.id,
              label: `${c.name} (${c.chart_type_display})`,
            }))}
          />
        )}
      </Modal>

      <ShareModal
        open={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        dashboardId={parseInt(id!)}
        isPublic={currentDashboard.is_public}
        isOwner={currentDashboard.is_owner}
        onTogglePublic={(isPublic) => {
          useDashboardStore.setState((state) => ({
            currentDashboard: state.currentDashboard
              ? { ...state.currentDashboard, is_public: isPublic }
              : null,
          }));
        }}
      />

      <FilterManager
        open={filterManagerOpen}
        onClose={() => setFilterManagerOpen(false)}
        dashboardId={parseInt(id!)}
        filters={currentDashboard.filters || []}
        onSaved={(filters) => {
          useDashboardStore.setState((state) => ({
            currentDashboard: state.currentDashboard
              ? { ...state.currentDashboard, filters }
              : null,
          }));
          const defaults: Record<string, string | number | null> = {};
          filters.forEach((f) => {
            if (f.defaultValue != null && f.defaultValue !== "") {
              defaults[f.id] = f.defaultValue;
            }
          });
          setFilterValues(defaults);
        }}
      />
    </div>
  );
}