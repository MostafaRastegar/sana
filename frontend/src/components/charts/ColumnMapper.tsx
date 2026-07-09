import { Select, Form } from "antd";
import type { Column, ChartType } from "../../types";

interface ColumnMapperProps {
  columns: Column[];
  chartType: ChartType;
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  aggregate: string;
  onXAxisChange: (value: string) => void;
  onYAxisChange: (value: string) => void;
  onGroupByChange: (value: string | undefined) => void;
  onAggregateChange: (value: string) => void;
}

const LABELS: Record<ChartType, { x: string; y: string; groupBy: boolean; aggregate: boolean }> = {
  bar: { x: "X Axis (Categories)", y: "Y Axis (Values)", groupBy: true, aggregate: true },
  line: { x: "X Axis (Categories)", y: "Y Axis (Values)", groupBy: true, aggregate: true },
  area: { x: "X Axis (Categories)", y: "Y Axis (Values)", groupBy: true, aggregate: true },
  pie: { x: "Label", y: "Value", groupBy: false, aggregate: true },
  scatter: { x: "X Value", y: "Y Value", groupBy: false, aggregate: false },
  heatmap: { x: "Row", y: "Column", groupBy: false, aggregate: false },
  kpi: { x: "Label", y: "Value", groupBy: false, aggregate: true },
};

export default function ColumnMapper({
  columns,
  chartType,
  xAxis,
  yAxis,
  groupBy,
  aggregate,
  onXAxisChange,
  onYAxisChange,
  onGroupByChange,
  onAggregateChange,
}: ColumnMapperProps) {
  const labels = LABELS[chartType] || LABELS.bar;

  const numericColumns = columns
    .filter((col) => ["integer", "decimal", "float", "number"].includes(col.type))
    .map((col) => ({ value: col.name, label: col.label || col.name }));

  const categoryColumns = columns
    .filter((col) => ["string", "text", "varchar", "boolean"].includes(col.type))
    .map((col) => ({ value: col.name, label: col.label || col.name }));

  const allOptions = columns.map((col) => ({
    value: col.name,
    label: col.label || col.name,
  }));

  const xOptions = chartType === "pie" || chartType === "heatmap"
    ? categoryColumns
    : chartType === "scatter"
      ? numericColumns
      : [...categoryColumns, ...allOptions];

  const yOptions = chartType === "scatter"
    ? numericColumns
    : numericColumns.length > 0
      ? numericColumns
      : allOptions;

  return (
    <div className="space-y-3">
      <Form.Item label={labels.x} className="mb-0">
        <Select
          value={xAxis || undefined}
          onChange={onXAxisChange}
          options={xOptions.length > 0 ? xOptions : allOptions}
          placeholder={`Select ${labels.x.toLowerCase()}`}
          allowClear
          showSearch
        />
      </Form.Item>
      <Form.Item label={labels.y} className="mb-0">
        <Select
          value={yAxis || undefined}
          onChange={onYAxisChange}
          options={yOptions.length > 0 ? yOptions : allOptions}
          placeholder={`Select ${labels.y.toLowerCase()}`}
          allowClear
          showSearch
        />
      </Form.Item>
      {labels.groupBy && (
        <Form.Item label="Group By (Optional)" className="mb-0">
          <Select
            value={groupBy || undefined}
            onChange={(val) => onGroupByChange(val)}
            options={categoryColumns}
            placeholder="Group by column"
            allowClear
            showSearch
          />
        </Form.Item>
      )}
      {labels.aggregate && (
        <Form.Item label="Aggregation" className="mb-0">
          <Select
            value={aggregate}
            onChange={onAggregateChange}
            options={
              chartType === "pie"
                ? [
                    { value: "sum", label: "Sum" },
                    { value: "count", label: "Count" },
                  ]
                : [
                    { value: "none", label: "None (Raw)" },
                    { value: "sum", label: "Sum" },
                    { value: "avg", label: "Average" },
                    { value: "count", label: "Count" },
                    { value: "min", label: "Minimum" },
                    { value: "max", label: "Maximum" },
                  ]
            }
          />
        </Form.Item>
      )}
    </div>
  );
}