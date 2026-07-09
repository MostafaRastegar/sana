import type { ChartType, ChartData } from "../types";

export function buildEChartsOption(
  chartType: ChartType,
  data: ChartData
): Record<string, unknown> {
  const { columns, rows, config } = data;

  if (!rows || rows.length === 0) {
    return {
      title: { text: "No data", left: "center" },
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value" },
      series: [],
    };
  }

  const xCol = config.xAxis || columns[0]?.name || "";
  const yCol = config.yAxis || columns[1]?.name || columns[0]?.name || "";
  const groupByCol = config.groupBy;

  const xAxisData = rows.map((r) => String(r[xCol] ?? ""));
  const yAxisData = rows.map((r) => Number(r[yCol] ?? 0));

  const baseOption = {
    tooltip: { trigger: "axis" as const },
    grid: { left: 60, right: 20, bottom: 60, top: 40 },
    xAxis: {
      type: "category" as const,
      data: xAxisData,
      axisLabel: { rotate: xAxisData.length > 10 ? 45 : 0 },
    },
    yAxis: { type: "value" as const },
  };

  if (chartType === "pie") {
    return {
      tooltip: { trigger: "item" as const, formatter: "{b}: {c} ({d}%)" },
      series: [
        {
          type: "pie",
          radius: ["0%", "70%"],
          center: ["50%", "50%"],
          data: xAxisData.map((name, i) => ({
            name,
            value: yAxisData[i],
          })),
          label: {
            show: true,
            formatter: "{b}: {c}",
          },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0, 0, 0, 0.5)" },
          },
        },
      ],
    };
  }

  if (chartType === "scatter") {
    return {
      tooltip: { trigger: "item" as const, formatter: (params: { name: string; value: number[] }) => `${params.name}<br/>X: ${params.value[0]}<br/>Y: ${params.value[1]}` },
      xAxis: { type: "value" as const },
      yAxis: { type: "value" as const },
      series: [
        {
          type: "scatter",
          data: rows.map((r) => [Number(r[xCol] ?? 0), Number(r[yCol] ?? 0)]),
          symbolSize: 12,
          itemStyle: { opacity: 0.7 },
        },
      ],
    };
  }

  if (chartType === "heatmap") {
    const values = rows.map((r) => Number(r[yCol] ?? 0));
    const max = Math.max(...values, 1);
    return {
      tooltip: { trigger: "item" as const },
      xAxis: { type: "category" as const, data: xAxisData, axisLabel: { rotate: 45 } },
      yAxis: { type: "category" as const, data: [yCol] },
      visualMap: { min: 0, max, inRange: { color: ["#f0f0f0", "#ff6b6b"] } },
      series: [
        {
          type: "heatmap",
          data: xAxisData.map((name, i) => [name, yCol, values[i]]),
          label: { show: true },
        },
      ],
    };
  }

  const series: Record<string, unknown>[] = [];
  if (groupByCol) {
    const groups = [...new Set(rows.map((r) => String(r[groupByCol] ?? "")))];
    for (const group of groups) {
      const groupRows = rows.filter((r) => String(r[groupByCol] ?? "") === group);
      series.push({
        name: group,
        type: chartType,
        stack: chartType === "area" ? "total" : undefined,
        data: xAxisData.map((x) => {
          const match = groupRows.find((r) => String(r[xCol] ?? "") === x);
          return match ? Number(match[yCol] ?? 0) : 0;
        }),
      });
    }
  } else {
    series.push({
      name: yCol,
      type: chartType,
      data: yAxisData,
      smooth: chartType === "line",
      areaStyle: chartType === "area" ? { opacity: 0.3 } : undefined,
      emphasis: { focus: "series" },
    });
  }

  return { ...baseOption, series };
}
