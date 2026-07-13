import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Spin, Descriptions, Tag, Button, Card, Table, Space, message } from "antd";
import { ArrowLeftOutlined, BellOutlined, CheckCircleOutlined, StopOutlined, ReloadOutlined } from "@ant-design/icons";
import { useAlertStore } from "../store/alertStore";

export default function AlertDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentAlert, alertHistory, loading, error, fetchAlertById, fetchAlertHistory, toggleAlert, checkAlertNow } = useAlertStore();

  useEffect(() => {
    if (id) {
      fetchAlertById(Number(id));
      fetchAlertHistory(Number(id));
    }
  }, [id, fetchAlertById, fetchAlertHistory]);

  const handleToggle = async () => {
    if (!currentAlert) return;
    await toggleAlert(currentAlert.id);
    message.success(currentAlert.is_active ? "Alert deactivated" : "Alert activated");
  };

  const handleCheckNow = async () => {
    if (!currentAlert) return;
    try {
      const result = await checkAlertNow(currentAlert.id);
      message.info(result?.message || "Check completed");
      fetchAlertHistory(currentAlert.id);
    } catch {
      message.error("Check failed");
    }
  };

  if (loading && !currentAlert) return <Spin className="block mx-auto mt-8" />;
  if (!currentAlert) return null;

  const historyColumns = [
    { title: "Triggered At", dataIndex: "triggered_at", key: "triggered_at", render: (v: string) => new Date(v).toLocaleString() },
    { title: "Actual Value", dataIndex: "actual_value", key: "actual_value", render: (v: number) => v.toLocaleString() },
    { title: "Threshold", dataIndex: "threshold", key: "threshold", render: (v: number) => v.toLocaleString() },
    { title: "Condition", dataIndex: "condition", key: "condition" },
    { title: "Message", dataIndex: "message", key: "message", ellipsis: true },
    {
      title: "Notified",
      dataIndex: "notification_sent",
      key: "notification_sent",
      render: (sent: boolean) => sent ? <Tag color="green">Sent</Tag> : <Tag color="default">No</Tag>,
    },
  ];

  return (
    <div>
      <Space className="mb-4">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/alerts")}>Back</Button>
      </Space>

      <Card
        title={
          <Space>
            <BellOutlined className="text-blue-500" />
            <span>{currentAlert.name}</span>
            <Tag color={currentAlert.is_active ? "green" : "red"}>{currentAlert.is_active ? "Active" : "Inactive"}</Tag>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleCheckNow}>Check Now</Button>
            <Button
              icon={currentAlert.is_active ? <StopOutlined /> : <CheckCircleOutlined />}
              onClick={handleToggle}
            >
              {currentAlert.is_active ? "Deactivate" : "Activate"}
            </Button>
          </Space>
        }
        className="mb-6"
      >
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Dataset">{currentAlert.dataset_name}</Descriptions.Item>
          <Descriptions.Item label="Metric">{currentAlert.metric}</Descriptions.Item>
          <Descriptions.Item label="Aggregation">{currentAlert.aggregation}</Descriptions.Item>
          <Descriptions.Item label="Condition">{currentAlert.condition_display}</Descriptions.Item>
          <Descriptions.Item label="Threshold">{currentAlert.threshold.toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Check Interval">{currentAlert.check_interval}</Descriptions.Item>
          <Descriptions.Item label="Created By">{currentAlert.created_by_name}</Descriptions.Item>
          <Descriptions.Item label="Last Checked">{currentAlert.last_checked ? new Date(currentAlert.last_checked).toLocaleString() : "Never"}</Descriptions.Item>
          <Descriptions.Item label="Last Triggered">{currentAlert.last_triggered ? new Date(currentAlert.last_triggered).toLocaleString() : "Never"}</Descriptions.Item>
          <Descriptions.Item label="Notification Channels">{(currentAlert.notification_channels || []).join(", ") || "None"}</Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>{currentAlert.description || "No description"}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Trigger History" className="mb-6">
        <Table
          dataSource={alertHistory}
          columns={historyColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: "No trigger history yet" }}
        />
      </Card>
    </div>
  );
}