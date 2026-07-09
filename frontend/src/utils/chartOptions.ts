import type { ChartType, ChartData } from "../types";

function buildGaugeOption(data: ChartData): Record<string, unknown> {
  const { config, columns, rows } = data;
  if (!rows?.length) return { title: { text: "No data", left: "center" } };

  const valueCol = config.yAxis || columns[0]?.name || "";
  const nameCol = config.xAxis || columns[1]?.name || "";
  const val = Number(rows[0]?.[valueCol] ?? 0);
  const name = nameCol ? String(rows[0]?.[nameCol] ?? "") : "Value";
  const max = config.limit ? Number(config.limit) : 100;

  return {
    tooltip: { formatter: `{b}: {c}` },
    series: [
      {
        type: "gauge",
        max,
        detail: { formatter: "{value}", fontSize: 16 },
        axisLine: {
          lineStyle: {
            width: 20,
            color: [
              [0.3, "#67e0e3"],
              [0.7, "#37a2da"],
              [1, "#fd666d"],
            ],
          },
        },
        pointer: { width: 6 },
        data: [{ value: val, name }],
      },
    ],
  };
}

function buildFunnelOption(data: ChartData): Record<string, unknown> {
  const { columns, rows, config } = data;
  if (!rows?.length) return { title: { text: "No data", left: "center" } };

  const nameCol = config.xAxis || columns[0]?.name || "";
  const valueCol = config.yAxis || columns[1]?.name || columns[0]?.name || "";

  return {
    tooltip: { trigger: "item", formatter: "{b}: {c}" },
    toolbox: { feature: { saveAsImage: {} } },
    series: [
      {
        type: "funnel",
        left: "10%",
        top: 40,
        bottom: 40,
        width: "80%",
        minSize: "0%",
        maxSize: "100%",
        sort: "descending",
        gap: 2,
        label: { show: true, position: "inside", formatter: "{b}: {c}" },
        labelLine: { length: 10 },
        data: rows.map((r) => ({
          name: String(r[nameCol] ?? ""),
          value: Number(r[valueCol] ?? 0),
        })),
      },
    ],
  };
}

function buildTreemapOption(data: ChartData): Record<string, unknown> {
  const { columns, rows, config } = data;
  if (!rows?.length) return { title: { text: "No data", left: "center" } };

  const nameCol = config.xAxis || columns[0]?.name || "";
  const valueCol = config.yAxis || columns[1]?.name || columns[0]?.name || "";
  const groupCol = config.groupBy;

  let dataItems: Record<string, unknown>[];

  if (groupCol) {
    // Two-level treemap: group → item
    const groups: Record<string, { name: string; value: number; children: { name: string; value: number }[] }> = {};
    for (const r of rows) {
      const g = String(r[groupCol] ?? "Other");
      if (!groups[g]) groups[g] = { name: g, value: 0, children: [] };
      const child = { name: String(r[nameCol] ?? ""), value: Number(r[valueCol] ?? 0) };
      groups[g].children.push(child);
      groups[g].value += child.value;
    }
    dataItems = Object.values(groups).map((g) => {
      // sum children value properly typed
      const total = g.children.reduce((s: number, c: { value: number }) => s + c.value, 0);
      return { name: g.name, value: total, children: g.children };
    });
  } else {
    dataItems = rows.map((r) => ({
      name: String(r[nameCol] ?? ""),
      value: Number(r[valueCol] ?? 0),
    }));
  }

  return {
    tooltip: { formatter: "{b}: {c}" },
    series: [
      {
        type: "treemap",
        roam: "zoom",
        leafDepth: 1,
        label: { show: true, formatter: "{b}" },
        data: dataItems,
      },
    ],
  };
}

function buildRadarOption(data: ChartData): Record<string, unknown> {
  const { columns, rows, config } = data;
  if (!rows?.length) return { title: { text: "No data", left: "center" } };

  const valueCol = config.yAxis || columns[1]?.name || columns[0]?.name || "";
  const nameCol = config.xAxis || columns[0]?.name || "";
  const groupCol = config.groupBy;

  // indicator: unique xAxis values with inferred max
  const xValues = [...new Set(rows.map((r) => String(r[nameCol] ?? "")))];
  const values = xValues.map((x) => {
    const match = rows.find((r) => String(r[nameCol] ?? "") === x);
    return Number(match?.[valueCol] ?? 0);
  });
  const maxVal = Math.max(...values, 1);

  const indicator = xValues.map((name) => ({ name, max: Math.ceil(maxVal * 1.2) }));

  if (groupCol) {
    // Multiple series by group
    const groups = [...new Set(rows.map((r) => String(r[groupCol] ?? "")))];
    const series = groups.map((g) => {
      const groupRows = rows.filter((r) => String(r[groupCol] ?? "") === g);
      const vals = xValues.map((x) => {
        const match = groupRows.find((r) => String(r[nameCol] ?? "") === x);
        return Number(match?.[valueCol] ?? 0);
      });
      return { value: vals, name: g };
    });
    return {
      tooltip: {},
      legend: { data: groups, bottom: 0 },
      radar: { indicator, radius: "65%" },
      series: [{ type: "radar", data: series }],
    };
  }

  // Single series
  return {
    tooltip: {},
    radar: { indicator, radius: "65%" },
    series: [
      {
        type: "radar",
        data: [{ value: values, name: "Data" }],
        areaStyle: { opacity: 0.25 },
      },
    ],
  };
}

export function buildEChartsOption(
  chartType: ChartType,
  data: ChartData
): Record<string, unknown> {
  if (chartType === "kpi") return {};

  // New chart types
  if (chartType === "gauge") return buildGaugeOption(data);
  if (chartType === "funnel") return buildFunnelOption(data);
  if (chartType === "treemap") return buildTreemapOption(data);
  if (chartType === "radar") return buildRadarOption(data);

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