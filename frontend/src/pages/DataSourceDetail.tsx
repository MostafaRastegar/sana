import { useEffect, useCallback, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Descriptions, Button, Tag, Spin, Table, message, Card, Space, Divider, Tabs, Typography,
} from "antd";
import {
  ArrowLeftOutlined, ApiOutlined, SyncOutlined, ReloadOutlined, UploadOutlined,
} from "@ant-design/icons";
import { useDatasourceStore } from "../store/datasourceStore";
import type { SyncLog } from "../types";

const sourceTypeColors: Record<string, string> = {
  postgresql: "blue", mysql: "orange", sqlite: "purple", api: "green", csv: "cyan",
};
const statusColors: Record<string, string> = {
  active: "success", error: "error", syncing: "processing",
};
const syncStatusColors: Record<string, string> = {
  success: "success", failed: "error", running: "processing",
};

export default function DataSourceDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentDatasource: ds, logs, records, loading,
    fetchDatasourceById, testConnection, sync, fetchLogs, fetchRecords,
  } = useDatasourceStore();

  const numericId = Number(id);

  useEffect(() => {
    if (numericId) {
      fetchDatasourceById(numericId);
      fetchLogs(numericId);
      fetchRecords(numericId);
    }
  }, [numericId, fetchDatasourceById, fetchLogs, fetchRecords]);

  const handleTest = useCallback(async () => {
    const result = await testConnection(numericId);
    if (result) message[result.success ? "success" : "error"](result.message);
  }, [numericId, testConnection]);

  const handleSync = useCallback(async () => {
    await sync(numericId);
    message.success("Sync triggered");
    fetchLogs(numericId);
    fetchRecords(numericId);
  }, [numericId, sync, fetchLogs, fetchRecords]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);

  const handleCsvImport = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const token = localStorage.getItem("access_token");
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`/api/datasources/${numericId}/import-csv/`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      const data = await res.json();
      if (res.ok) message.success(data.message || "Import started");
      else message.error(data.error || "Import failed");
      fetchLogs(numericId);
      fetchRecords(numericId);
    } catch {
      message.error("Import failed");
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [numericId, fetchLogs, fetchRecords]);

  const handleRefresh = useCallback(() => {
    fetchDatasourceById(numericId);
    fetchLogs(numericId);
    fetchRecords(numericId);
  }, [numericId, fetchDatasourceById, fetchLogs, fetchRecords]);

  if (loading || !ds) return <Spin className="flex justify-center mt-20" size="large" />;

  const logColumns = [
    { title: "Status", dataIndex: "status", key: "status", render: (s: string) => <Tag color={syncStatusColors[s]}>{s}</Tag> },
    { title: "Started", dataIndex: "started_at", key: "started_at", render: (v: string) => new Date(v).toLocaleString() },
    { title: "Finished", dataIndex: "finished_at", key: "finished_at", render: (v: string | null) => v ? new Date(v).toLocaleString() : "-" },
    { title: "Rows", dataIndex: "rows_imported", key: "rows_imported" },
    { title: "Error", dataIndex: "error_message", key: "error_message", render: (v: string) => v || "-" },
  ];

  const recordColumns = (records?.columns || []).map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    render: (v: unknown) => (v == null ? "" : String(v)),
  }));

  const tabItems = [
    {
      key: "records",
      label: `Data Records${records?.row_count != null ? ` (${records.row_count.toLocaleString()})` : ""}`,
      children: (
        <Table
          dataSource={records?.rows || []}
          columns={recordColumns}
          rowKey={(_, i) => String(i)}
          pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `${t} records` }}
          size="small"
          scroll={{ x: "max-content" }}
        />
      ),
    },
    {
      key: "logs",
      label: "Sync Logs",
      children: (
        <Table
          dataSource={logs}
          columns={logColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
  ];

  return (
    <div>
      <Space className="mb-4">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/datasources")}>Back</Button>
      </Space>

      <Card>
        <Descriptions title={ds.name} bordered column={2} size="small">
          <Descriptions.Item label="Type">
            <Tag color={sourceTypeColors[ds.source_type]}>{ds.source_type}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={statusColors[ds.status]}>{ds.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Last Synced" span={2}>
            {ds.last_synced ? new Date(ds.last_synced).toLocaleString() : "Never"}
          </Descriptions.Item>
          <Descriptions.Item label="Sync Schedule" span={2}>
            {ds.sync_schedule || "-"}
          </Descriptions.Item>
          <Descriptions.Item label="Error Message" span={2}>
            {ds.error_message || "-"}
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <Space>
          <Button icon={<ApiOutlined />} onClick={handleTest}>Test Connection</Button>
          <Button type="primary" icon={<SyncOutlined />} onClick={handleSync}>Sync Now</Button>
          {ds.source_type === "csv" && (
            <>
              <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleCsvImport} />
              <Button icon={<UploadOutlined />} loading={importing} onClick={() => fileInputRef.current?.click()}>Import CSV</Button>
            </>
          )}
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>Refresh</Button>
        </Space>
      </Card>

      <Card className="mt-4">
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
}