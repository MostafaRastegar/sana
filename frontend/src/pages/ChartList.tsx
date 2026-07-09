import { useEffect } from "react";
import { Card, Button, Spin, Alert, Tag, Modal, message } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useChartStore } from "../store/chartStore";
import { CHART_TYPES } from "../utils/constants";

export default function ChartList() {
  const navigate = useNavigate();
  const { charts, loading, error, fetchCharts, deleteChart } = useChartStore();

  useEffect(() => {
    fetchCharts();
  }, [fetchCharts]);

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: "Delete chart?",
      content: "This action cannot be undone.",
      onOk: async () => {
        await deleteChart(id);
        message.success("Chart deleted");
      },
    });
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (error) return <Alert type="error" message={error} className="m-4" />;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Charts</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/charts/new")}>
          New Chart
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {charts.map((chart) => (
          <Card
            key={chart.id}
            title={chart.name}
            hoverable
            onClick={() => navigate(`/charts/${chart.id}`)}
            actions={[
              <EditOutlined key="edit" onClick={(e) => { e.stopPropagation(); navigate(`/charts/${chart.id}`); }} />,
              <DeleteOutlined key="delete" onClick={(e) => { e.stopPropagation(); handleDelete(chart.id); }} />,
            ]}
          >
            <p className="text-gray-500 min-h-[40px]">{chart.description || "No description"}</p>
            <Tag color="blue">
              {CHART_TYPES.find((t) => t.value === chart.chart_type)?.label || chart.chart_type}
            </Tag>
            <p className="text-gray-500 mt-2">Dataset: {chart.dataset_name}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
