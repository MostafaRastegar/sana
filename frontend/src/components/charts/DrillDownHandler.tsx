import { useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { fetchChartDrillDown } from "../../api/charts";
import type { DrillDownConfig, ChartData, ChartConfig } from "../../types";

interface DrillStep {
  column: string;
  value: string;
  chartId: number;
  label: string;
}

interface DrillDownHandlerProps {
  chartId: number;
  config: DrillDownConfig | null | undefined;
  chartConfig?: ChartConfig | null;
  onDrill?: (chartId: number, data: ChartData) => void;
  onDrillStep?: (step: DrillStep) => void;
}

function rawToChartData(raw: { columns: { name: string; type: string; label: string }[]; rows: Record<string, unknown>[]; chart_type?: string; config?: Record<string, unknown> }): ChartData {
  return {
    columns: raw.columns,
    rows: raw.rows,
    chart_type: (raw.chart_type || "bar") as ChartData["chart_type"],
    config: (raw.config as unknown as ChartConfig) || ({} as ChartConfig),
  };
}

export function useDrillDown({ chartId, config, chartConfig, onDrill, onDrillStep }: DrillDownHandlerProps) {
  const navigate = useNavigate();

  const handleDrill = useCallback(async (column: string, value: string) => {
    if (!config?.enabled) return;

    const targetChartId = config.target_chart ?? undefined;
    const targetDashboardId = config.target_dashboard ?? undefined;

    if (targetDashboardId) {
      navigate(`/dashboards/${targetDashboardId}`);
      return;
    }

    if (targetChartId) {
      try {
        const raw = await fetchChartDrillDown(chartId, column, value, targetChartId);
        const chartData = rawToChartData(raw);
        if (onDrillStep) {
          onDrillStep({ column, value, chartId: targetChartId, label: `${column}=${value}` });
        }
        if (onDrill) {
          onDrill(chartId, chartData);
        }
      } catch {
        // silent
      }
      return;
    }

    try {
      const raw = await fetchChartDrillDown(chartId, column, value);
      const chartData = rawToChartData(raw);
      if (onDrillStep) {
        onDrillStep({ column, value, chartId, label: `${column}=${value}` });
      }
      if (onDrill) {
        onDrill(chartId, chartData);
      }
    } catch {
      // silent
    }
  }, [chartId, config, navigate, onDrill, onDrillStep]);

  const chartClickEvents = useMemo(
    () =>
      config?.enabled
        ? {
            click: (params: { name?: string; value?: string | number | Array<string | number>; seriesName?: string }) => {
              // For scatter: params.name is the x-axis category label, but we need the raw x value.
              // ECharts pie: params.name = slice name.
              // Use drill_column from config, else xAxis from chart config, else "name".
              const col = config.drill_column || chartConfig?.xAxis || "name";
              // For scatter with items that have _rawX, use that; else params.name
              const rawX = params.value && Array.isArray(params.value) ? params.value[0] : undefined;
              const val = String(rawX ?? params.name ?? params.value ?? "");
              if (val) handleDrill(col, val);
            },
          }
        : undefined,
    [config?.enabled, config?.drill_column, chartConfig?.xAxis, handleDrill],
  );

  return { handleDrill, chartClickEvents };
}