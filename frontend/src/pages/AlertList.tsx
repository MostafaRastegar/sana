import { useEffect, useState, useCallback } from "react";
import { Table, Button, Spin, Alert as AntAlert, Space, Modal, Input, Select, Switch, message } from "antd";
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, BellOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useAlertStore } from "../store/alertStore";
import { fetchDatasets, detectTableColumns } from "../api/datasets";
import type { DataAlert, AlertCondition, AlertAggregation, AlertInterval, Dataset } from "../types";

const CONDITIONS: { value: AlertCondition; label: string }[] = [
  { value: "above", label: "Above" },
  { value: "below", label: "Below" },
  { value: "equals", label: "Equals" },
  { value: "change_percent", label: "Percent Change" },
];

const AGGREGATIONS: { value: AlertAggregation; label: string }[] = [
  { value: "sum", label: "Sum" },
  { value: "avg", label: "Average" },
  { value: "count", label: "Count" },
  { value: "min", label: "Min" },
  { value: "max", label: "Max" },
];

const INTERVALS: { value: AlertInterval; label: string }[] = [
  { value: "hourly", label: "Hourly" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

const CHANNELS = ["email", "sms", "webhook"];

interface FormState {
  name: string;
  description: string;
  dataset: number | null;
  metric: string;
  aggregation: AlertAggregation;
  condition: AlertCondition;
  threshold: number;
  check_interval: AlertInterval;
  notification_channels: string[];
}

const EMPTY_FORM: FormState = {
  name: "",
  description: "",
  dataset: null,
  metric: "",
  aggregation: "sum",
  condition: "above",
  threshold: 0,
  check_interval: "daily",
  notification_channels: ["email"],
};

export default function AlertList() {
  const navigate = useNavigate();
  const { alerts, loading, error, fetchAlerts, createAlert, updateAlert, deleteAlert, fetchAlertStats, stats } = useAlertStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [metricColumns, setMetricColumns] = useState<{ name: string; type: string; label: string }[]>([]);

  useEffect(() => {
    fetchAlerts();
    fetchAlertStats();
    fetchDatasets().then((d) => setDatasets(d.results)).catch(() => {});
  }, [fetchAlerts, fetchAlertStats]);

  const handleDatasetChange = (datasetId: number | null) => {
    setForm({ ...form, dataset: datasetId, metric: "" });
    setMetricColumns([]);
    if (!datasetId) return;
    const ds = datasets.find((d) => d.id === datasetId);
    if (ds?.table_name) {
      detectTableColumns(ds.table_name).then((res) => setMetricColumns(res.columns)).catch(() => setMetricColumns([]));
    }
  };

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (a: DataAlert) => {
    setEditingId(a.id);
    setForm({
      name: a.name,
      description: a.description,
      dataset: a.dataset,
      metric: a.metric,
      aggregation: a.aggregation,
      condition: a.condition,
      threshold: a.threshold,
      check_interval: a.check_interval,
      notification_channels: a.notification_channels,
    });
    setModalOpen(true);
    // load columns for the selected dataset
    if (a.dataset) {
      const ds = datasets.find((d) => d.id === a.dataset);
      if (ds?.table_name) {
        detectTableColumns(ds.table_name).then((res) => setMetricColumns(res.columns)).catch(() => setMetricColumns([]));
      }
    }
  };

  const handleSave = async () => {
    if (!form.name.trim()) { message.error("Name is required"); return; }
    if (!form.dataset) { message.error("Dataset is required"); return; }
    if (!form.metric.trim()) { message.error("Metric is required"); return; }
    setSaving(true);
    try {
      const payload = { ...form, dataset: form.dataset };
      if (editingId) {
        await updateAlert(editingId, payload);
        message.success("Alert updated");
      } else {
        await createAlert(payload as Partial<DataAlert>);
        message.success("Alert created");
      }
      setModalOpen(false);
    } catch {
      message.error("Failed to save alert");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: "Delete alert?",
      content: "This action cannot be undone.",
      onOk: async () => {
        await deleteAlert(id);
        message.success("Alert deleted");
      },
    });
  };

  if (loading && alerts.length === 0) return <Spin className="block mx-auto mt-8" />;
  if (error) return <AntAlert type="error" message={error} className="m-4" />;

  const tableColumns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, record: { id: number }) => (
        <Button type="link" className="p-0" onClick={() => navigate(`/alerts/${record.id}`)}>
          {name}
        </Button>
      ),
    },
    { title: "Dataset", dataIndex: "dataset_name", key: "dataset_name" },
    { title: "Metric", dataIndex: "metric", key: "metric" },
    { title: "Condition", dataIndex: "condition_display", key: "condition" },
    { title: "Threshold", dataIndex: "threshold", key: "threshold", render: (v: number) => v.toLocaleString() },
    { title: "Interval", dataIndex: "check_interval", key: "check_interval" },
    {
      title: "Active",
      dataIndex: "is_active",
      key: "is_active",
      render: (active: boolean) => (
        <span className={active ? "text-green-600" : "text-red-500"}>{active ? "Yes" : "No"}</span>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: DataAlert) => (
        <Space>
          <Button icon={<EyeOutlined />} size="small" onClick={() => navigate(`/alerts/${record.id}`)} />
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(record)} />
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDelete(record.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Stats cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="text-sm text-gray-500">Total Alerts</div>
          <div className="text-2xl font-bold">{stats?.total_alerts ?? 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="text-sm text-gray-500">Active</div>
          <div className="text-2xl font-bold text-green-600">{stats?.active_alerts ?? 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="text-sm text-gray-500">Triggered (24h)</div>
          <div className="text-2xl font-bold text-orange-600">{stats?.triggered_last_24h ?? 0}</div>
        </div>
      </div>

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Alerts</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Alert
        </Button>
      </div>

      <Table dataSource={alerts} columns={tableColumns} rowKey="id" pagination={{ pageSize: 10 }} />

      <Modal
        title={editingId ? "Edit Alert" : "New Alert"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        width={600}
      >
        <div className="space-y-3">
          <div>
            <label className="block mb-1 text-sm font-medium">Name</label>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Alert name" />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Description</label>
            <Input.TextArea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Dataset</label>
            <Select
              className="w-full"
              value={form.dataset}
              onChange={handleDatasetChange}
              placeholder="Select dataset"
            >
              {datasets.map((d) => (
                <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 text-sm font-medium">Metric (column)</label>
              <Select
                className="w-full"
                value={form.metric || undefined}
                onChange={(v) => setForm({ ...form, metric: v })}
                placeholder="Select metric column"
                notFoundContent={form.dataset ? "No columns found" : "Select a dataset first"}
              >
                {metricColumns.map((col) => (
                  <Select.Option key={col.name} value={col.name}>{col.label}</Select.Option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block mb-1 text-sm font-medium">Aggregation</label>
              <Select className="w-full" value={form.aggregation} onChange={(v) => setForm({ ...form, aggregation: v })}>
                {AGGREGATIONS.map((a) => (
                  <Select.Option key={a.value} value={a.value}>{a.label}</Select.Option>
                ))}
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 text-sm font-medium">Condition</label>
              <Select className="w-full" value={form.condition} onChange={(v) => setForm({ ...form, condition: v })}>
                {CONDITIONS.map((c) => (
                  <Select.Option key={c.value} value={c.value}>{c.label}</Select.Option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block mb-1 text-sm font-medium">Threshold</label>
              <Input type="number" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 text-sm font-medium">Check Interval</label>
              <Select className="w-full" value={form.check_interval} onChange={(v) => setForm({ ...form, check_interval: v })}>
                {INTERVALS.map((i) => (
                  <Select.Option key={i.value} value={i.value}>{i.label}</Select.Option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block mb-1 text-sm font-medium">Notification</label>
              <Select
                mode="multiple"
                className="w-full"
                value={form.notification_channels}
                onChange={(v) => setForm({ ...form, notification_channels: v })}
                placeholder="Select channels"
              >
                {CHANNELS.map((ch) => (
                  <Select.Option key={ch} value={ch}>{ch.toUpperCase()}</Select.Option>
                ))}
              </Select>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}