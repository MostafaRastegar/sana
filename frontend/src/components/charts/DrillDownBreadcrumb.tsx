import { Breadcrumb, Button } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";

interface DrillStep {
  column: string;
  value: string;
  chartId: number;
  label: string;
}

interface DrillDownBreadcrumbProps {
  steps: DrillStep[];
  onNavigateUp: (index: number) => void;
  onReset: () => void;
}

export default function DrillDownBreadcrumb({ steps, onNavigateUp, onReset }: DrillDownBreadcrumbProps) {
  if (steps.length === 0) return null;

  const items = steps.map((s, i) => ({
    key: String(i),
    title: (
      <span
        className="cursor-pointer text-blue-600 hover:text-blue-800"
        onClick={() => onNavigateUp(i)}
      >
        {s.label}
      </span>
    ),
  }));

  return (
    <div className="flex items-center gap-2 mb-2">
      <Button size="small" icon={<ArrowLeftOutlined />} onClick={onReset}>
        Reset
      </Button>
      <Breadcrumb items={items} />
    </div>
  );
}