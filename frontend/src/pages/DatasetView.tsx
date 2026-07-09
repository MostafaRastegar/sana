import { useEffect, useState } from "react";
import { Spin, Alert, Button, Table, Card, Descriptions, Tag, Space, Modal, message } from "antd";
import { ArrowLeftOutlined, ReloadOutlined, DeleteOutlined } from "@ant-design/icons";
import { useParams, useNavigate } from "react-router-dom";
import { useDatasetStore } from "../store/datasetStore";

export default function DatasetView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentDataset, datasetData, loading, error, fetchDatasetById, fetchDatasetData, deleteDataset } = useDatasetStore();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    if (id) {
      fetchDatasetById(parseInt(id));
    }
  }, [id, fetchDatasetById]);

  useEffect(() => {
    if (id) {
      fetchDatasetData(parseInt(id), page, pageSize);
    }
  }, [id, page, pageSize, fetchDatasetData]);

  const handleDelete = () => {
    if (!currentDataset) return;
    Modal.confirm({
      title: "Delete this dataset?",
      content: "This action cannot be undone.",
      onOk: async () => {
        await deleteDataset(currentDataset.id);
        message.success("Dataset deleted");
        navigate("/datasets");
      },
    });
  };

  if (loading && !currentDataset) return <Spin className="block mx-auto mt-8" />;
  if (error) return <Alert type="error" message={error} className="m-4" />;
  if (!currentDataset) return <Alert type="warning" message="Dataset not found" className="m-4" />;

  const dataColumns = datasetData?.columns.map((col) => ({
    title: col.label,
    dataIndex: col.name,
    key: col.name,
    ellipsis: true,
  })) || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/datasets")}>
            Back
          </Button>
          <h2 className="text-2xl font-bold mb-0">{currentDataset.name}</h2>
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => fetchDatasetById(parseInt(id!))}>
            Refresh
          </Button>
          <Button icon={<DeleteOutlined />} danger onClick={handleDelete}>
            Delete
          </Button>
        </Space>
      </div>

      <Card className="mb-4">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Table">
            <Tag color="blue">{currentDataset.table_name}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Row Count">
            <Tag>{currentDataset.row_count ?? "N/A"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Columns">
            <Tag>{currentDataset.column_count}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            {new Date(currentDataset.created_at).toLocaleDateString()}
          </Descriptions.Item>
          {currentDataset.description && (
            <Descriptions.Item label="Description" span={2}>
              {currentDataset.description}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {currentDataset.columns && currentDataset.columns.length > 0 && (
        <Card title={`Columns (${currentDataset.columns.length})`} className="mb-4">
          <Table
            dataSource={currentDataset.columns.map((c, i) => ({ ...c, key: i }))}
            columns={[
              { title: "Name", dataIndex: "name", key: "name" },
              { title: "Type", dataIndex: "type", key: "type", render: (t: string) => <Tag>{t}</Tag> },
              { title: "Label", dataIndex: "label", key: "label" },
            ]}
            pagination={false}
            size="small"
          />
        </Card>
      )}

      <Card title="Data Browser">
        {datasetData ? (
          <Table
            dataSource={datasetData.rows}
            columns={dataColumns}
            rowKey={(_, index) => String(index)}
            pagination={{
              current: page,
              pageSize: pageSize,
              total: datasetData.total,
              showSizeChanger: true,
              onChange: (p, ps) => { setPage(p); setPageSize(ps); },
            }}
            size="small"
            scroll={{ x: "max-content" }}
          />
        ) : (
          <Alert type="info" message="No data available for this table. Ensure the backing table exists." />
        )}
      </Card>
    </div>
  );
}
