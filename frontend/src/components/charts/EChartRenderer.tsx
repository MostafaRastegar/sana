import ReactECharts from "echarts-for-react";
import clsx from "clsx";

interface EChartRendererProps {
  option: Record<string, unknown>;
  height?: number | string;
  width?: number | string;
  loading?: boolean;
  className?: string;
}

export default function EChartRenderer({
  option,
  height = 400,
  width = "100%",
  loading = false,
  className,
}: EChartRendererProps) {
  const defaultOption = {
    title: { text: "No data" },
    tooltip: {},
    xAxis: { type: "category", data: [] },
    yAxis: { type: "value" },
    series: [],
  };

  const chartOption = option && Object.keys(option).length > 0 ? option : defaultOption;

  return (
    <div className={clsx('h-full', className)}>
      <ReactECharts
        option={chartOption}
        style={{ height, width }}
        showLoading={loading}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
}