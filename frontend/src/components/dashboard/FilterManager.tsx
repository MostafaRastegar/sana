import { useState, useEffect } from "react";
import { Modal, Button, Input, Select, message } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import type { DashboardFilter } from "../../types";
import { updateDashboardFilters } from "../../api/dashboards";
import { fetchDatasets } from "../../api/datasets";

interface FilterManagerProps {
  open: boolean;
  onClose: () => void;
  dashboardId: number;
  filters: DashboardFilter[];
  onSaved: (filters: DashboardFilter[]) => void;
}

interface DatasetOption {
  id: number;
  name: string;
  columns: { name: string; type: string; label: string }[];
}

export function FilterManager({
  open,
  onClose,
  dashboardId,
  filters,
  onSaved,
}: FilterManagerProps) {
  const [items, setItems] = useState<DashboardFilter[]>(() =>
    filters.length > 0
      ? filters
      : [{ id: crypto.randomUUID(), name: "", type: "text", column: "", dataset: null, defaultValue: null, options: [] }]
  );
  const [saving, setSaving] = useState(false);
  const [datasets, setDatasets] = useState<DatasetOption[]>([]);

  useEffect(() => {
    if (open) {
      fetchDatasets().then((res) => {
        setDatasets(res.results.map((d) => ({ id: d.id, name: d.name, columns: d.columns || [] })));
      });
    }
  }, [open]);

  const selectedDataset = (index: number) =>
    datasets.find((d) => d.id === items[index]?.dataset);

  const updateItem = (index: number, patch: Partial<DashboardFilter>) => {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  const addItem = () => {
    setItems((prev) => [
      ...prev,
      { id: crypto.randomUUID(), name: "", type: "text", column: "", dataset: null, defaultValue: null, options: [] },
    ]);
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    const valid = items.filter((f) => f.name && f.column);
    setSaving(true);
    try {
      const updated = await updateDashboardFilters(dashboardId, valid as unknown as Record<string, unknown>[]);
      onSaved(updated.filters);
      message.success("Filters saved");
      onClose();
    } catch {
      message.error("Failed to save filters");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Manage Filters"
      open={open}
      onCancel={onClose}
      width={720}
      footer={
        <div className="flex justify-between">
          <Button onClick={addItem} icon={<PlusOutlined />}>
            Add Filter
          </Button>
          <div className="space-x-2">
            <Button onClick={onClose}>Cancel</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>
              Save Filters
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4 max-h-[60vh] overflow-y-auto">
        {items.length === 0 && (
          <p className="text-gray-400 text-center py-8">No filters. Click "Add Filter" to create one.</p>
        )}
        {items.map((f, i) => (
          <div key={f.id} className="border rounded-lg p-4 space-y-3 bg-gray-50 dark:bg-gray-800">
            <div className="flex justify-between items-center">
              <span className="text-xs font-medium text-gray-500 uppercase">Filter #{i + 1}</span>
              <Button danger size="small" icon={<DeleteOutlined />} onClick={() => removeItem(i)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
                <Input
                  size="small"
                  placeholder="e.g. Region"
                  value={f.name}
                  onChange={(e) => updateItem(i, { name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Dataset</label>
                <Select
                  className="w-full"
                  size="small"
                  placeholder="Select dataset..."
                  allowClear
                  value={f.dataset}
                  onChange={(val) => updateItem(i, { dataset: val, column: "" })}
                  options={datasets.map((d) => ({ value: d.id, label: d.name }))}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Column</label>
                {f.dataset && selectedDataset(i) ? (
                  <Select
                    className="w-full"
                    size="small"
                    placeholder="Select column..."
                    value={f.column || undefined}
                    onChange={(val) => updateItem(i, { column: val })}
                    options={selectedDataset(i)!.columns.map((c) => ({
                      value: c.name,
                      label: `${c.label} (${c.name})`,
                    }))}
                  />
                ) : (
                  <Input
                    size="small"
                    placeholder="e.g. region"
                    value={f.column}
                    onChange={(e) => updateItem(i, { column: e.target.value })}
                  />
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                <Select
                  className="w-full"
                  size="small"
                  value={f.type}
                  onChange={(val) => updateItem(i, { type: val, operator: val === "number" ? "eq" : undefined })}
                  options={[
                    { value: "text", label: "Text" },
                    { value: "select", label: "Select (Dropdown)" },
                    { value: "date", label: "Date" },
                    { value: "daterange", label: "Date Range" },
                    { value: "number", label: "Number" },
                  ]}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {f.type === "select" && (
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Options (one per line)
                  </label>
                  <Input.TextArea
                    size="small"
                    rows={3}
                    placeholder="Option1&#10;Option2&#10;Option3"
                    value={(f.options || []).join("\n")}
                    onChange={(e) =>
                      updateItem(i, {
                        options: e.target.value
                          .split("\n")
                          .map((s) => s.trim())
                      })
                    }
                  />
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Default Value
                </label>
                <Input
                  size="small"
                  placeholder="Optional"
                  value={f.defaultValue ?? ""}
                  onChange={(e) => updateItem(i, { defaultValue: e.target.value || null })}
                />
              </div>
              {f.type === "number" && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Operator
                  </label>
                  <Select
                    className="w-full"
                    size="small"
                    value={f.operator || "eq"}
                    onChange={(val) => updateItem(i, { operator: val as "eq" | "neq" | "gt" | "gte" | "lt" | "lte" })}
                    options={[
                      { value: "eq", label: "Equals (=)" },
                      { value: "neq", label: "Not equals (≠)" },
                      { value: "gt", label: "Greater than (>) " },
                      { value: "gte", label: "Greater than or equals (≥)" },
                      { value: "lt", label: "Less than (<)" },
                      { value: "lte", label: "Less than or equals (≤)" },
                    ]}
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
}