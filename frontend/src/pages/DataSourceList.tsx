import { useEffect, useState, useRef } from "react";
import {
  Table, Button, Modal, Input, Select, Tag, Space, message, Popconfirm, Typography,
} from "antd";
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined, SyncOutlined, UploadOutlined, DatabaseOutlined,
} from "@ant-design/icons";
import { useDatasourceStore } from "../store/datasourceStore";
import { useDatasetStore } from "../store/datasetStore";
import type { DataSource, SourceType } from "../types";

const sourceTypeColors: Record<string, string> = {
  postgresql: "blue",
  mysql: "orange",
  sqlite: "purple",
  api: "green",
  csv: "cyan",
};

const statusColors: Record<string, string> = {
  active: "success",
  error: "error",
  syncing: "processing",
};

const configFields: Record<SourceType, { key: string; label: string }[]> = {
  postgresql: [
    { key: "host", label: "Host" },
    { key: "port", label: "Port" },
    { key: "database", label: "Database" },
    { key: "user", label: "User" },
    { key: "password", label: "Password" },
  ],
  mysql: [
    { key: "host", label: "Host" },
    { key: "port", label: "Port" },
    { key: "database", label: "Database" },
    { key: "user", label: "User" },
    { key: "password", label: "Password" },
  ],
  sqlite: [
    { key: "path", label: "File Path" },
  ],
  api: [
    { key: "url", label: "URL" },
    { key: "headers", label: "Headers (JSON)" },
    { key: "results_key", label: "Results Key" },
  ],
  csv: [
    { key: "csv_content", label: "CSV Content" },
  ],
};

export default function DataSourceList() {
  const { datasources, loading, fetchDatasources, createDatasource, updateDatasource, deleteDatasource, testConnection, error } = useDatasourceStore();
  const { createFromDatasource } = useDatasetStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DataSource | null>(null);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState<SourceType>("postgresql");
  const [syncSchedule, setSyncSchedule] = useState("");
  const [config, setConfig] = useState<Record<string, string>>({});
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { fetchDatasources(); }, [fetchDatasources]);

  const openCreate = () => {
    setEditing(null);
    setName("");
    setSourceType("postgresql");
    setSyncSchedule("");
    setConfig({});
    setCsvFile(null);
    setModalOpen(true);
  };

  const openEdit = (ds: DataSource) => {
    setEditing(ds);
    setName(ds.name);
    setSourceType(ds.source_type);
    setSyncSchedule(ds.sync_schedule);
    setConfig(Object.fromEntries(
      Object.entries(ds.connection_config).map(([k, v]) => [k, String(v ?? "")])
    ));
    setModalOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (sourceType === "csv" && csvFile && !editing) {
        // Two-step process for CSV:
        // 1. Create datasource via JSON (no file — avoids multipart issues with axios)
        const ds = await createDatasource({
          name,
          source_type: sourceType,
          sync_schedule: syncSchedule,
        } as Partial<DataSource>);
        if (!ds) throw new Error("Failed to create datasource");
        // 2. Upload CSV file via the dedicated import-csv endpoint (has MultiPartParser)
        const { uploadCsvFile } = await import("../api/datasources");
        await uploadCsvFile(ds.id, csvFile);
      } else {
        const payload = {
          name,
          source_type: sourceType,
          sync_schedule: syncSchedule,
          connection_config: config,
        };
        if (editing) {
          await updateDatasource(editing.id, payload);
        } else {
          await createDatasource(payload);
        }
      }
      setModalOpen(false);
      message.success(editing ? "Updated" : "Created");
    } catch {
      message.error("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDatasource(id);
      message.success("Deleted");
    } catch {
      message.error("Failed to delete");
    }
  };

  const handleTest = async (id: number) => {
    const result = await testConnection(id);
    if (result) {
      message[result.success ? "success" : "error"](result.message);
    }
  };

  const handleCreateDataset = async (id: number) => {
    try {
      const result = await useDatasetStore.getState().createFromDatasource(id);
      if (result) {
        message.success(`Dataset "${result.name}" created`);
      }
    } catch {
      message.error("Failed to create dataset");
    }
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, record: DataSource) => (
        <Typography.Link href={`/datasources/${record.id}`}>{name}</Typography.Link>
      ),
    },
    {
      title: "Type",
      dataIndex: "source_type",
      key: "source_type",
      render: (t: SourceType) => <Tag color={sourceTypeColors[t]}>{t}</Tag>,
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (s: string) => <Tag color={statusColors[s]}>{s}</Tag>,
    },
    {
      title: "Last Synced",
      dataIndex: "last_synced",
      key: "last_synced",
      render: (v: string | null) => v ? new Date(v).toLocaleString() : "-",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: DataSource) => (
        <Space>
          <Button size="small" icon={<ApiOutlined />} onClick={() => handleTest(record.id)}>
            Test
          </Button>
          <Button size="small" icon={<SyncOutlined />} onClick={() => useDatasourceStore.getState().sync(record.id)}>
            Sync
          </Button>
          <Button size="small" icon={<DatabaseOutlined />} onClick={() => handleCreateDataset(record.id)}>
            Dataset
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="Delete?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Data Sources</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Data Source
        </Button>
      </div>

      <Table
        dataSource={datasources}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editing ? "Edit Data Source" : "New Data Source"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        width={560}
      >
        <div className="space-y-3">
          <div>
            <label className="block mb-1 text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My DB" />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Type</label>
            <Select className="w-full" value={sourceType} onChange={(v) => { setSourceType(v); setConfig({}); }}>
              <Select.Option value="postgresql">PostgreSQL</Select.Option>
              <Select.Option value="mysql">MySQL</Select.Option>
              <Select.Option value="sqlite">SQLite</Select.Option>
              <Select.Option value="api">REST API</Select.Option>
              <Select.Option value="csv">CSV File</Select.Option>
            </Select>
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Sync Schedule</label>
            <Input value={syncSchedule} onChange={(e) => setSyncSchedule(e.target.value)} placeholder="hourly / daily / weekly / cron" />
          </div>
          {sourceType === "csv" && !editing && (
            <div>
              <label className="block mb-1 text-sm font-medium">CSV File</label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => { if (e.target.files?.[0]) setCsvFile(e.target.files[0]); }}
              />
              <Button icon={<UploadOutlined />} onClick={() => fileInputRef.current?.click()}>
                {csvFile ? csvFile.name : "Choose CSV file"}
              </Button>
            </div>
          )}
          {configFields[sourceType]?.filter(f => f.key !== "csv_content").map((field) => (
            <div key={field.key}>
              <label className="block mb-1 text-sm font-medium">{field.label}</label>
              {field.key === "headers" ? (
                <Input.TextArea
                  value={config[field.key] ?? ""}
                  onChange={(e) => setConfig((c) => ({ ...c, [field.key]: e.target.value }))}
                  rows={2}
                  placeholder='{"Authorization": "Bearer ..."}'
                />
              ) : (
                <Input
                  value={config[field.key] ?? ""}
                  onChange={(e) => setConfig((c) => ({ ...c, [field.key]: e.target.value }))}
                  placeholder={field.key === "password" ? "••••••••" : ""}
                  type={field.key === "password" ? "password" : "text"}
                />
              )}
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
}