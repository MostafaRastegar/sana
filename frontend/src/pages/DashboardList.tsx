import { useEffect, useState } from "react";
import { Card, Button, Spin, Alert, Modal, Input, message, Row, Col, Tag } from "antd";
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ShareAltOutlined, GlobalOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useDashboardStore } from "../store/dashboardStore";

export default function DashboardList() {
  const navigate = useNavigate();
  const { dashboards, loading, error, fetchDashboards, createDashboard, updateDashboard, deleteDashboard } = useDashboardStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDashboard, setEditingDashboard] = useState<{ id: number; name: string; description: string } | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchDashboards();
  }, [fetchDashboards]);

  const openCreate = () => {
    setEditingDashboard(null);
    setName("");
    setDescription("");
    setModalOpen(true);
  };

  const openEdit = (d: { id: number; name: string; description: string }) => {
    setEditingDashboard(d);
    setName(d.name);
    setDescription(d.description);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      message.error("Name is required");
      return;
    }
    setSaving(true);
    try {
      if (editingDashboard) {
        await updateDashboard(editingDashboard.id, { name, description });
        message.success("Dashboard updated");
      } else {
        const created = await createDashboard({ name, description });
        if (created) {
          message.success("Dashboard created");
          navigate(`/dashboards/${created.id}`);
        }
      }
      setModalOpen(false);
    } catch {
      message.error("Failed to save dashboard");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: "Delete dashboard?",
      content: "This action cannot be undone.",
      onOk: async () => {
        await deleteDashboard(id);
        message.success("Dashboard deleted");
      },
    });
  };

  if (loading) return <Spin className="block mx-auto mt-8" />;
  if (error) return <Alert type="error" message={error} className="m-4" />;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Dashboards</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Dashboard
        </Button>
      </div>
      {dashboards.length === 0 ? (
        <div className="bg-gray-50 h-64 flex items-center justify-center rounded-lg border-2 border-dashed">
          <div className="text-center">
            <p className="text-gray-400 mb-2">No dashboards yet</p>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              Create Your First Dashboard
            </Button>
          </div>
        </div>
      ) : (
        <Row gutter={[16, 16]}>
          {dashboards.map((dashboard) => (
            <Col xs={24} sm={12} lg={8} key={dashboard.id}>
              <Card
                hoverable
                title={
                  <div className="flex items-center gap-1">
                    <span className="truncate">{dashboard.name}</span>
                    {dashboard.is_public && <GlobalOutlined className="text-green-500 text-xs" />}
                    {dashboard.user_permission && dashboard.user_permission !== "admin" && (
                      <Tag color={dashboard.user_permission === "edit" ? "blue" : "green"} className="text-xs leading-none">
                        {dashboard.user_permission.toUpperCase()}
                      </Tag>
                    )}
                  </div>
                }
                actions={[
                  <EyeOutlined key="view" onClick={() => navigate(`/dashboards/${dashboard.id}`)} />,
                  <EditOutlined key="edit" onClick={() => openEdit(dashboard)} />,
                  <DeleteOutlined key="delete" onClick={() => handleDelete(dashboard.id)} />,
                ]}
              >
                <p className="text-gray-500 min-h-[40px]">
                  {dashboard.description || "No description"}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-blue-500 text-sm">
                    {dashboard.chart_count} chart{dashboard.chart_count !== 1 ? "s" : ""}
                  </span>
                  {dashboard.shared_users_count > 0 && (
                    <span className="text-gray-400 text-xs flex items-center gap-1">
                      <ShareAltOutlined /> {dashboard.shared_users_count}
                    </span>
                  )}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
      <Modal
        title={editingDashboard ? "Edit Dashboard" : "New Dashboard"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
      >
        <div className="space-y-3">
          <div>
            <label className="block mb-1 text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Dashboard name"
            />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium">Description</label>
            <Input.TextArea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={3}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
