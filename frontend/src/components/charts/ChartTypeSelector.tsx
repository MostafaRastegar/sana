import { Radio, Tag, Space } from "antd";
import { CHART_TYPES } from "../../utils/constants";
import type { ChartType } from "../../types";

interface ChartTypeSelectorProps {
  value: ChartType;
  onChange: (value: ChartType) => void;
}

const chartIcons: Record<string, string> = {
  bar: "📊",
  line: "📈",
  pie: "🥧",
  scatter: "✨",
  area: "🏔️",
  heatmap: "🔥",
  kpi: "🎯",
  gauge: "🔄",
  funnel: "🔽",
  treemap: "🧩",
  radar: "🕸️",
};

export default function ChartTypeSelector({ value, onChange }: ChartTypeSelectorProps) {
  return (
    <div>
      <Radio.Group
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full"
      >
        <Space orientation="vertical" className="w-full">
          <div className="grid grid-cols-3 gap-2">
            {CHART_TYPES.map((t) => (
              <div key={t.value} className="flex justify-center h-20 p-2">
              <Radio.Button
                key={t.value}
                value={t.value}
                className={`text-center p-2 h-auto border-0 ${
                  value === t.value ? "border-blue-500" : ""
                }`}
              >
                <div className="text-xl mb-1">{chartIcons[t.value]}</div>
                <div>{t.label}</div>
              </Radio.Button>
              </div>
            ))}
          </div>
        </Space>
      </Radio.Group>
      {value && (
        <div className="mt-2">
          <Tag color="blue">{CHART_TYPES.find((t) => t.value === value)?.label || value}</Tag>
        </div>
      )}
    </div>
  );
}
