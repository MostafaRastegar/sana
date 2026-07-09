import { Card, Spin, Alert } from "antd";
import EChartRenderer from "./EChartRenderer";
import { buildEChartsOption } from "../../utils/chartOptions";
import type { ChartData } from "../../types";

interface ChartPreviewProps {
  data: ChartData | null;
  loading: boolean;
  error: string | null;
}

export default function ChartPreview({ data, loading, error }: ChartPreviewProps) {
  if (loading) {
    return (
      <Card title="Preview">
        <div className="h-80 flex items-center justify-center">
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Preview">
        <Alert type="error" message={error} />
      </Card>
    );
  }

  if (!data || !data.rows || data.rows.length === 0) {
    return (
      <Card title="Preview">
        <div className="h-80 flex items-center justify-center text-gray-400">
          <p>Configure your chart to see a preview</p>
        </div>
      </Card>
    );
  }

  const option = buildEChartsOption(data.chart_type, data);

  return (
    <Card title="Preview">
      <EChartRenderer option={option} height={350} />
      <div className="mt-2 text-xs text-gray-400">
        {data.rows.length} data points
      </div>
    </Card>
  );
}
