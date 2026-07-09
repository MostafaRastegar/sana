import { Select, Input, Button, Space } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import type { Column, Filter } from "../../types";
import { FILTER_OPERATORS } from "../../utils/constants";

interface FilterBuilderProps {
  columns: Column[];
  filters: Filter[];
  onChange: (filters: Filter[]) => void;
}

export default function FilterBuilder({ columns, filters, onChange }: FilterBuilderProps) {
  const columnOptions = columns.map((col) => ({
    value: col.name,
    label: col.label || col.name,
  }));

  const handleAdd = () => {
    const newFilter: Filter = {
      column: columns[0]?.name || "",
      operator: "eq",
      value: "",
    };
    onChange([...filters, newFilter]);
  };

  const handleRemove = (index: number) => {
    onChange(filters.filter((_, i) => i !== index));
  };

  const handleUpdate = (index: number, field: keyof Filter, value: unknown) => {
    const updated = filters.map((f, i) =>
      i === index ? { ...f, [field]: value } : f
    );
    onChange(updated);
  };

  return (
    <div>
      <div className="space-y-2">
        {filters.map((filter, index) => (
          <Space key={index} className="w-full" align="start">
            <Select
              value={filter.column}
              onChange={(val) => handleUpdate(index, "column", val)}
              options={columnOptions}
              placeholder="Column"
              style={{ width: 150 }}
              showSearch
            />
            <Select
              value={filter.operator}
              onChange={(val) => handleUpdate(index, "operator", val)}
              options={FILTER_OPERATORS.map((op) => ({
                value: op.value,
                label: op.label,
              }))}
              style={{ width: 140 }}
            />
            <Input
              value={String(filter.value)}
              onChange={(e) => handleUpdate(index, "value", e.target.value)}
              placeholder="Value"
              style={{ width: 150 }}
            />
            <Button
              icon={<DeleteOutlined />}
              onClick={() => handleRemove(index)}
              danger
              size="small"
            />
          </Space>
        ))}
      </div>
      <Button
        type="dashed"
        onClick={handleAdd}
        icon={<PlusOutlined />}
        className="mt-2"
        block
      >
        Add Filter
      </Button>
    </div>
  );
}
