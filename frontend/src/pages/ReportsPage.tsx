import { useEffect, useState } from "react";
import {
  Table, Button, Spin, Alert as AntAlert, Space, Modal, Input, Select,
  Switch, InputNumber, message, Tooltip,
} from "antd";
import {
  PlusOutlined, PlayCircleOutlined, DeleteOutlined, ScheduleOutlined,
  EyeOutlined, HistoryOutlined, DownloadOutlined,
} from "@ant-design/icons";
import {
  fetchReports, createReport, updateReport, deleteReport, triggerNow, toggleReport,
  fetchReportHistory, downloadReport,
} from "../api/reports";
import { fetchDashboards } from "../api/dashboards";
import type { ScheduledReport, Dashboard, ReportFrequency, ReportFormat, ReportHistory } from "../types";

const FREQUENCIES: { value: ReportFrequency; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

const FORMATS: { value: ReportFormat; label: string }[] = [
  { value: "pdf", label: "PDF" },
  { value: "email_html", label: "HTML Email" },
];

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

interface FormState {
  name: string;
  description: string;
  dashboard: number | null;
  format: ReportFormat;
  frequency: ReportFrequency;
  day_of_week: number | null;
  day_of_month: number | null;
  time: string;
  timezone: string;
  recipients: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  description: "",
  dashboard: null,
  format: "pdf",
  frequency: "daily",
  day_of_week: null,
  day_of_month: null,
  time: "08:00",
  timezone: "UTC",
  recipients: "",
};

export default function ReportsPage() {
  const [reports, setReports] = useState<ScheduledReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [historyData, setHistoryData] = useState<ReportHistory[]>([]);
  const [selectedReportName, setSelectedReportName] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [r, d] = await Promise.all([
        fetchReports(),
        fetchDashboards({ page_size: 100 }),
      ]);
      setReports(r.results);
      setDashboards(d.results);
    } catch (e) {
      setError("Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (r: ScheduledReport) => {
    setEditingId(r.id);
    setForm({
      name: r.name,
      description: r.description,
      dashboard: r.dashboard,
      format: r.format,
      frequency: r.frequency,
      day_of_week: r.day_of_week,
      day_of_month: r.day_of_month,
      time: r.time,
      timezone: r.timezone,
      recipients: "",
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) { message.error("Name is required"); return; }
    if (!form.dashboard) { message.error("Dashboard is required"); return; }
    setSaving(true);
    try {
      const payload = {
        ...form,
        dashboard: form.dashboard,
        recipients: form.recipients
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
          .map(Number),
      };
      if (editingId) {
        await updateReport(editingId, payload);
        message.success("Report updated");
      } else {
        await createReport(payload as Partial<ScheduledReport>);
        message.success("Report created");
      }
      setModalOpen(false);
      load();
    } catch {
      message.error("Failed to save report");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: "Delete report?",
      onOk: async () => {
        await deleteReport(id);
        message.success("Report deleted");
        load();
      },
    });
  };

  const handleTrigger = async (id: number) => {
    try {
      const res = await triggerNow(id);
      message.success(res.message);
    } catch {
      message.error("Failed to trigger report");
    }
  };

  const handleToggle = async (id: number) => {
    await toggleReport(id);
    load();
  };

  const handleShowHistory = async (id: number, name: string) => {
    try {
      const data = await fetchReportHistory(id);
      setHistoryData(data);
      setSelectedReportName(name);
      setHistoryModalOpen(true);
    } catch {
      message.error("Failed to load history");
    }
  };

  const handleDownload = async (id: number, name: string) => {
    try {
      const response = await downloadReport(id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${name}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      message.error("Failed to download report");
    }
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (error) return <AntAlert type="error" message={error} className="m-4" />;

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Dashboard",
      dataIndex: "dashboard_name",
      key: "dashboard_name",
    },
    {
      title: "Frequency",
      dataIndex: "frequency",
      key: "frequency",
      render: (f: string, r: ScheduledReport) => {
        if (f === "weekly" && r.day_of_week !== null) return `Weekly (${WEEKDAYS[r.day_of_week]})`;
        if (f === "monthly" && r.day_of_month !== null) return `Monthly (day ${r.day_of_month})`;
        return "Daily";
      },
    },
    {
      title: "Time",
      dataIndex: "time",
      key: "time",
    },
    {
      title: "Format",
      dataIndex: "format",
      key: "format",
    },
    {
      title: "Recipients",
      dataIndex: "recipients_count",
      key: "recipients_count",
    },
    {
      title: "Active",
      dataIndex: "is_active",
      key: "is_active",
      render: (active: boolean, r: ScheduledReport) => (
        <Switch checked={active} onChange={() => handleToggle(r.id)} size="small" />
      ),
    },
    {
      title: "Last Sent",
      dataIndex: "last_sent",
      key: "last_sent",
      render: (v: string | null) => {
        if (!v) return "-";
        const d = new Date(v);
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
      },
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, r: ScheduledReport) => (
        <Space>
          <Tooltip title="Preview">
            <Button
              icon={<EyeOutlined />}
              size="small"
              onClick={() => window.open(`/api/reports/${r.id}/preview/`, "_blank")}
            />
          </Tooltip>
          <Tooltip title="Download PDF">
            <Button icon={<DownloadOutlined />} size="small" onClick={() => handleDownload(r.id, r.name)} />
          </Tooltip>
          <Tooltip title="History">
            <Button icon={<HistoryOutlined />} size="small" onClick={() => handleShowHistory(r.id, r.name)} />
          </Tooltip>
          <Tooltip title="Send now">
            <Button icon={<PlayCircleOutlined />} size="small" onClick={() => handleTrigger(r.id)} />
          </Tooltip>
          <Button icon={<ScheduleOutlined />} size="small" onClick={() => openEdit(r)} />
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDelete(r.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Scheduled Reports</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Report
        </Button>
      </div>

      <Table dataSource={reports} columns={columns} rowKey="id" pagination={{ pageSize: 10 }} />

      <Modal
        title={editingId ? "Edit Report" : "New Report"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        width={600}
      >
        <div className="space-y-3">
          <div>
            <label className="block mb-1 text-sm font-medium">Name</label>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Description</label>
            <Input.TextArea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Dashboard</label>
            <Select className="w-full" value={form.dashboard} onChange={(v) => setForm({ ...form, dashboard: v })} placeholder="Select dashboard">
              {dashboards.map((d) => (
                <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 text-sm font-medium">Format</label>
              <Select className="w-full" value={form.format} onChange={(v) => setForm({ ...form, format: v })}>
                {FORMATS.map((f) => (
                  <Select.Option key={f.value} value={f.value}>{f.label}</Select.Option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block mb-1 text-sm font-medium">Frequency</label>
              <Select className="w-full" value={form.frequency} onChange={(v) => setForm({ ...form, frequency: v, day_of_week: null, day_of_month: null })}>
                {FREQUENCIES.map((f) => (
                  <Select.Option key={f.value} value={f.value}>{f.label}</Select.Option>
                ))}
              </Select>
            </div>
          </div>
          {form.frequency === "weekly" && (
            <div>
              <label className="block mb-1 text-sm font-medium">Day of Week</label>
              <Select className="w-full" value={form.day_of_week} onChange={(v) => setForm({ ...form, day_of_week: v })} placeholder="Select day">
                {WEEKDAYS.map((d, i) => (
                  <Select.Option key={i} value={i}>{d}</Select.Option>
                ))}
              </Select>
            </div>
          )}
          {form.frequency === "monthly" && (
            <div>
              <label className="block mb-1 text-sm font-medium">Day of Month</label>
              <InputNumber min={1} max={31} className="w-full" value={form.day_of_month} onChange={(v) => setForm({ ...form, day_of_month: v })} />
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 text-sm font-medium">Time</label>
              <Input
                value={form.time}
                onChange={(e) => setForm({ ...form, time: e.target.value })}
                placeholder="HH:mm (e.g. 08:00)"
              />
            </div>
            <div>
              <label className="block mb-1 text-sm font-medium">Timezone</label>
              <Input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} placeholder="UTC" />
            </div>
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Recipient IDs (comma-separated)</label>
            <Input
              value={form.recipients}
              onChange={(e) => setForm({ ...form, recipients: e.target.value })}
              placeholder="e.g. 1, 2, 3"
            />
          </div>
        </div>
      </Modal>

      <Modal
        title={`History: ${selectedReportName}`}
        open={historyModalOpen}
        onCancel={() => setHistoryModalOpen(false)}
        footer={null}
        width={700}
      >
        {historyData.length === 0 ? (
          <p className="text-gray-500">No history yet.</p>
        ) : (
          <Table
            dataSource={historyData}
            rowKey="id"
            pagination={false}
            columns={[
              { title: "Sent At", dataIndex: "sent_at", key: "sent_at", render: (v: string) => new Date(v).toLocaleString() },
              { title: "Status", dataIndex: "status", key: "status", render: (v: string) => (
                <span className={v === "sent" ? "text-green-600" : "text-red-600"}>{v}</span>
              )},
              { title: "Recipients", dataIndex: "recipients_count", key: "recipients_count" },
              { title: "Format", dataIndex: "format", key: "format" },
              { title: "Error", dataIndex: "error_message", key: "error_message", render: (v: string | undefined) => v || "-" },
            ]}
          />
        )}
      </Modal>
    </div>
  );
}
