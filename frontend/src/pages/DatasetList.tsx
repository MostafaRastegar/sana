import { useEffect, useState, useCallback } from "react";
import { Table, Button, Spin, Alert, Space, Modal, Input, Select, message, Tag } from "antd";
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, DatabaseOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useDatasetStore } from "../store/datasetStore";
import { fetchTables, detectTableColumns } from "../api/datasets";
import { useDatasourceStore } from "../store/datasourceStore";
import type { DataSource } from "../types";

export default function DatasetList() {
  const navigate = useNavigate();
  const { datasets, loading, error, fetchDatasets, createDataset, updateDataset, deleteDataset } = useDatasetStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDataset, setEditingDataset] = useState<{ id: number; name: string; description: string; table_name: string } | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tableName, setTableName] = useState("");
  const [detectedColumns, setDetectedColumns] = useState<{ name: string; type: string; label: string }[]>([]);
  const [tableOptions, setTableOptions] = useState<string[]>([]);
  const [columnsLoading, setColumnsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [datasourceId, setDatasourceId] = useState<number | null>(null);
  const [datasourceOptions, setDatasourceOptions] = useState<{ id: number; name: string; source_type: string }[]>([]);

  const loadDatasources = useCallback(async () => {
    try {
      const res = await useDatasourceStore.getState().fetchDatasources();
      const state = useDatasourceStore.getState();
      setDatasourceOptions(state.datasources.map((ds) => ({ id: ds.id, name: ds.name, source_type: ds.source_type })));
    } catch {
      // silently fail
    }
  }, []);

  const loadTables = useCallback(async () => {
    try {
      const res = await fetchTables();
      setTableOptions(res.tables);
    } catch {
      // silently fail — user can still type manually if needed
    }
  }, []);

  useEffect(() => {
    fetchDatasets();
    loadTables();
    loadDatasources();
  }, [fetchDatasets, loadTables, loadDatasources]);

  const openCreate = () => {
    setEditingDataset(null);
    setName("");
    setDescription("");
    setTableName("");
    setDetectedColumns([]);
    setDatasourceId(null);
    setModalOpen(true);
  };

  const openEdit = (d: { id: number; name: string; description: string; table_name: string }) => {
    setEditingDataset(d);
    setName(d.name);
    setDescription(d.description);
    setTableName(d.table_name);
    setDetectedColumns([]);
    setDatasourceId(null);
    setModalOpen(true);
  };

  const handleTableChange = async (value: string) => {
    setTableName(value);
    setDetectedColumns([]);
    if (!value) return;
    setColumnsLoading(true);
    try {
      const res = await detectTableColumns(value);
      setDetectedColumns(res.columns);
    } catch {
      message.warning("Could not detect columns for this table");
    } finally {
      setColumnsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!name.trim() || !tableName.trim()) {
      message.error("Name and Table Name are required");
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        name,
        description,
        table_name: tableName,
        columns: detectedColumns.length > 0 ? detectedColumns : undefined,
      };
      if (datasourceId) {
        payload.datasource = datasourceId;
      }
      if (editingDataset) {
        await updateDataset(editingDataset.id, payload);
        message.success("Dataset updated");
      } else {
        await createDataset(payload);
        message.success("Dataset created");
      }
      setModalOpen(false);
    } catch {
      message.error("Failed to save dataset");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: "Delete dataset?",
      content: "This action cannot be undone.",
      onOk: async () => {
        await deleteDataset(id);
        message.success("Dataset deleted");
      },
    });
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (error) return <Alert type="error" message={error} className="m-4" />;

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, record: { id: number }) => (
        <Button type="link" className="p-0" onClick={() => navigate(`/datasets/${record.id}`)}>
          {name}
        </Button>
      ),
    },
    { title: "Table", dataIndex: "table_name", key: "table_name" },
    { title: "Columns", dataIndex: "column_count", key: "column_count" },
    { title: "Row Count", dataIndex: "row_count", key: "row_count" },
    {
      title: "Data Source",
      dataIndex: "datasource_name",
      key: "datasource_name",
      render: (v: string | null) => v ? <Tag icon={<DatabaseOutlined />} color="blue">{v}</Tag> : "-",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: { id: number; name: string; description: string; table_name: string }) => (
        <Space>
          <Button icon={<EyeOutlined />} size="small" onClick={() => navigate(`/datasets/${record.id}`)} />
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(record)} />
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDelete(record.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Datasets</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Dataset
        </Button>
      </div>
      <Table
        dataSource={datasets}
        columns={columns}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingDataset ? "Edit Dataset" : "New Dataset"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
      >
        <div className="space-y-3">
          <div>
            <label className="block mb-1 text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Dataset name" />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Description</label>
            <Input.TextArea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" rows={2} />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Data Source (optional)</label>
            <Select
              className="w-full"
              value={datasourceId}
              onChange={(v) => setDatasourceId(v)}
              placeholder="Link to a data source"
              allowClear
            >
              {datasourceOptions.map((ds) => (
                <Select.Option key={ds.id} value={ds.id}>
                  <DatabaseOutlined className="mr-1" /> {ds.name} ({ds.source_type})
                </Select.Option>
              ))}
            </Select>
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Table</label>
            <Select
              showSearch
              className="w-full"
              value={tableName || undefined}
              onChange={handleTableChange}
              placeholder="Select or type a table name"
              loading={columnsLoading}
              notFoundContent={null}
              dropdownRender={(menu) => (
                <>
                  {menu}
                  <div className="p-2 text-xs text-gray-400 border-t mt-1">
                    {tableOptions.length === 0 ? "No tables found" : `${tableOptions.length} tables available`}
                  </div>
                </>
              )}
            >
              {tableOptions.map((t) => (
                <Select.Option key={t} value={t}>
                  {t}
                </Select.Option>
              ))}
            </Select>
          </div>
          {detectedColumns.length > 0 && (
            <div>
              <label className="block mb-1 text-sm font-medium">
                Detected Columns ({detectedColumns.length})
              </label>
              <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded max-h-24 overflow-y-auto">
                {detectedColumns.map((c) => (
                  <span key={c.name} className="inline-block mr-2 mb-1 bg-blue-50 px-2 py-0.5 rounded">
                    {c.name} <span className="text-gray-400">({c.type})</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
