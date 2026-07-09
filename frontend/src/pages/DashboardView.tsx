import { useEffect, useState, useCallback } from "react";
import { Spin, Alert, Button, Modal, Select, message } from "antd";
import { EditOutlined, PlusOutlined, SaveOutlined } from "@ant-design/icons";
import { useDashboardStore } from "../store/dashboardStore";
import { useChartStore } from "../store/chartStore";
import { useParams, useNavigate } from "react-router-dom";
import GridLayout from "react-grid-layout";
import EChartRenderer from "../components/charts/EChartRenderer";
import { buildEChartsOption } from "../utils/chartOptions";
import { fetchChartData } from "../api/charts";
import type { Chart, ChartData } from "../types";
import "react-grid-layout/css/styles.css";

interface ChartWithData {
  chart: Chart;
  data: ChartData | null;
  loading: boolean;
}

export default function DashboardView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentDashboard, loading, error, fetchDashboardById, updateLayout } = useDashboardStore();
  const { charts, fetchCharts } = useChartStore();
  const [chartDataMap, setChartDataMap] = useState<Record<number, ChartWithData>>({});
  const [isEditing, setIsEditing] = useState(false);
  const [layout, setLayout] = useState<{ i: string; x: number; y: number; w: number; h: number }[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      fetchDashboardById(parseInt(id));
      fetchCharts();
    }
  }, [id, fetchDashboardById, fetchCharts]);

  useEffect(() => {
    if (currentDashboard?.layout?.charts) {
      const gridLayout = currentDashboard.layout.charts.map((c) => ({
        i: String(c.chartId),
        x: c.x,
        y: c.y,
        w: c.w,
        h: c.h,
      }));
      setLayout(gridLayout);

      const chartIds = currentDashboard.layout.charts.map((c) => c.chartId);
      chartIds.forEach((chartId) => {
        if (!chartDataMap[chartId]) {
          loadChartData(chartId);
        }
      });
    }
  }, [currentDashboard]);

  const loadChartData = async (chartId: number) => {
    setChartDataMap((prev) => ({ ...prev, [chartId]: { ...prev[chartId], loading: true } }));
    try {
      const data = await fetchChartData(chartId);
      const chart = charts.find((c) => c.id === chartId);
      if (chart) {
        setChartDataMap((prev) => ({
          ...prev,
          [chartId]: { chart, data, loading: false },
        }));
      }
    } catch {
      setChartDataMap((prev) => ({
        ...prev,
        [chartId]: { ...prev[chartId], loading: false },
      }));
    }
  };

  const handleLayoutChange = useCallback((newLayout: { i: string; x: number; y: number; w: number; h: number }[]) => {
    if (isEditing) {
      setLayout(newLayout);
    }
  }, [isEditing]);

  const handleSaveLayout = async () => {
    if (!id) return;
    setSaving(true);
    const dashboardLayout = {
      charts: layout.map((item) => ({
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
    const maxY = layout.reduce((max, item) => Math.max(max, item.y + item.h), 0);
    setLayout([
      ...layout,
      { i: String(chartId), x: 0, y: maxY, w: 6, h: 4 },
    ]);
    loadChartData(chartId);
    setAddModalOpen(false);
  };

  const handleRemoveChart = (chartId: string) => {
    setLayout(layout.filter((item) => item.i !== chartId));
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (error) return <Alert type="error" message={error} className="m-4" />;
  if (!currentDashboard) return <Alert type="info" message="Dashboard not found" className="m-4" />;

  const addedChartIds = layout.map((l) => parseInt(l.i));
  const availableCharts = charts.filter((c) => !addedChartIds.includes(c.id));

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold">{currentDashboard.name}</h2>
          {currentDashboard.description && (
            <p className="text-gray-500">{currentDashboard.description}</p>
          )}
        </div>
        <div className="space-x-2">
          {!isEditing ? (
            <Button icon={<EditOutlined />} onClick={() => setIsEditing(true)}>
              Edit Layout
            </Button>
          ) : (
            <>
              <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
                Add Chart
              </Button>
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveLayout} loading={saving}>
                Save Layout
              </Button>
              <Button onClick={() => setIsEditing(false)}>Cancel</Button>
            </>
          )}
        </div>
      </div>

      {layout.length === 0 ? (
        <div className="bg-gray-50 h-96 flex items-center justify-center rounded-lg border-2 border-dashed">
          <div className="text-center">
            <p className="text-gray-400 mb-2">No charts in this dashboard</p>
            <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
              Add Chart
            </Button>
          </div>
        </div>
      ) : (
        <GridLayout
          className="layout"
          layout={layout}
          cols={12}
          rowHeight={100}
          width={1200}
          onLayoutChange={handleLayoutChange}
          isDraggable={isEditing}
          isResizable={isEditing}
          compactType="vertical"
        >
          {layout.map((item) => {
            const chartId = parseInt(item.i);
            const chartInfo = charts.find((c) => c.id === chartId);
            const dataWrapper = chartDataMap[chartId];
            const chartOption = dataWrapper?.data
              ? buildEChartsOption(dataWrapper.data.chart_type, dataWrapper.data)
              : {};

            return (
              <div key={item.i} className="bg-white rounded-lg shadow-sm border overflow-hidden">
                <div className="flex justify-between items-center px-3 py-2 bg-gray-50 border-b">
                  <span className="font-medium text-sm truncate">
                    {chartInfo?.name || `Chart #${chartId}`}
                  </span>
                  {isEditing && (
                    <Button
                      danger
                      size="small"
                      onClick={() => handleRemoveChart(item.i)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
                <div className="p-2 h-[calc(100%-40px)]">
                  {dataWrapper?.loading ? (
                    <div className="h-full flex items-center justify-center">
                      <Spin />
                    </div>
                  ) : (
                    <EChartRenderer
                      option={chartOption as Record<string, unknown>}
                      height="100%"
                    />
                  )}
                </div>
              </div>
            );
          })}
        </GridLayout>
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
            options={availableCharts.map((c) => ({
              value: c.id,
              label: `${c.name} (${c.chart_type_display})`,
            }))}
          />
        )}
      </Modal>
    </div>
  );
}
