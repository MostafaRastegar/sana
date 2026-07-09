import { useState, useEffect } from "react";
import { Button, Table, Spin, Alert, Select, Space, message, Modal, Input } from "antd";
import { PlayCircleOutlined, SaveOutlined, DownloadOutlined, DeleteOutlined } from "@ant-design/icons";
import MonacoEditor from "@monaco-editor/react";
import client from "../api/client";
import type { QueryResult, SavedQuery } from "../types";

export default function SQLEditor() {
  const [sql, setSql] = useState("SELECT * FROM demo_orders LIMIT 20;");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [selectedQueryId, setSelectedQueryId] = useState<number | null>(null);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveName, setSaveName] = useState("");

  useEffect(() => {
    loadSavedQueries();
  }, []);

  const loadSavedQueries = async () => {
    try {
      const { data } = await client.get("/queries/");
      setSavedQueries(data.results || data || []);
    } catch {
      // silently fail
    }
  };

  const executeQuery = async () => {
    if (!sql.trim()) {
      message.error("Please enter a SQL query");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { data } = await client.post("/execute/", { sql });
      setResult(data);
    } catch (err) {
      setError((err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message || (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuery = async () => {
    if (!saveName.trim()) return;
    try {
      await client.post("/queries/", { name: saveName, sql });
      message.success("Query saved");
      setSaveModalOpen(false);
      setSaveName("");
      loadSavedQueries();
    } catch {
      message.error("Failed to save query");
    }
  };

  const handleLoadQuery = (queryId: number) => {
    const query = savedQueries.find((q) => q.id === queryId);
    if (query) {
      setSql(query.sql);
      setSelectedQueryId(queryId);
      message.info(`Loaded: ${query.name}`);
    }
  };

  const handleDeleteQuery = async (queryId: number) => {
    try {
      await client.delete(`/queries/${queryId}/`);
      message.success("Query deleted");
      loadSavedQueries();
      if (selectedQueryId === queryId) setSelectedQueryId(null);
    } catch {
      message.error("Failed to delete query");
    }
  };

  const exportCSV = () => {
    if (!result || !result.rows.length) return;
    const headers = result.columns.map((c) => c.name);
    const csvRows = [
      headers.join(","),
      ...result.rows.map((row) =>
        headers.map((h) => {
          const val = row[h];
          const str = String(val ?? "");
          return str.includes(",") ? `"${str}"` : str;
        }).join(",")
      ),
    ];
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "query_results.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const tableColumns = result?.columns.map((col) => ({
    title: col.label,
    dataIndex: col.name,
    key: col.name,
    ellipsis: true,
  })) || [];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">SQL Editor</h2>
        <Space>
          {savedQueries.length > 0 && (
            <Select
              value={selectedQueryId}
              placeholder="Load saved query..."
              style={{ width: 200 }}
              onChange={handleLoadQuery}
              allowClear
              options={savedQueries.map((q) => ({ value: q.id, label: q.name }))}
            />
          )}
        </Space>
      </div>

      <div className="mb-4 border rounded overflow-hidden">
        <MonacoEditor
          height="200px"
          language="sql"
          value={sql}
          onChange={(value) => setSql(value || "")}
          theme="vs"
          options={{
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
          }}
        />
      </div>

      <Space className="mb-4">
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={executeQuery}
          loading={loading}
        >
          Execute
        </Button>
        <Button icon={<SaveOutlined />} onClick={() => setSaveModalOpen(true)}>
          Save Query
        </Button>
        {result && result.rows.length > 0 && (
          <Button icon={<DownloadOutlined />} onClick={exportCSV}>
            Export CSV
          </Button>
        )}
      </Space>

      {error && <Alert type="error" message={error} className="mb-4" closable />}
      {loading && <Spin className="block my-4" />}

      {result && (
        <div>
          <div className="text-sm text-gray-500 mb-2">
            {result.total} rows returned (showing {result.rows.length})
          </div>
          <div className="overflow-x-auto">
            <Table
              dataSource={result.rows}
              columns={tableColumns}
              rowKey={(_, index) => String(index)}
              pagination={{
                pageSize: result.page_size || 20,
                total: result.total,
                showSizeChanger: true,
                showTotal: (total) => `${total} rows`,
              }}
              size="small"
              bordered
              scroll={{ x: "max-content" }}
            />
          </div>
        </div>
      )}

      <Modal
        title="Save Query"
        open={saveModalOpen}
        onOk={handleSaveQuery}
        onCancel={() => setSaveModalOpen(false)}
      >
        <Input
          value={saveName}
          onChange={(e) => setSaveName(e.target.value)}
          placeholder="Query name"
        />
      </Modal>
    </div>
  );
}
