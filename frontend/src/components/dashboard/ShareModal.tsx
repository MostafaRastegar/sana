import { useEffect, useState } from "react";
import { Modal, Select, Button, Tag, message, Switch, Space, Empty, Spin, Typography } from "antd";
import {
  fetchDashboardPermissions,
  shareDashboard,
  unshareDashboard,
  toggleDashboardPublic,
  searchUsers,
} from "../../api/dashboards";
import type { DashboardPermission, DashboardPermissionLevel, UserSearchResult } from "../../types";
import { UserAddOutlined, CloseOutlined } from "@ant-design/icons";

const { Text } = Typography;

const PERMISSION_OPTIONS: { value: DashboardPermissionLevel; label: string }[] = [
  { value: "view", label: "View" },
  { value: "edit", label: "Edit" },
  { value: "admin", label: "Admin" },
];

interface ShareModalProps {
  open: boolean;
  onClose: () => void;
  dashboardId: number;
  isPublic: boolean;
  isOwner: boolean;
  onTogglePublic: (isPublic: boolean) => void;
}

export default function ShareModal({
  open,
  onClose,
  dashboardId,
  isPublic,
  isOwner,
  onTogglePublic,
}: ShareModalProps) {
  const [permissions, setPermissions] = useState<DashboardPermission[]>([]);
  const [loading, setLoading] = useState(false);
  const [userSearchResults, setUserSearchResults] = useState<UserSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedPermission, setSelectedPermission] = useState<DashboardPermissionLevel>("view");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && dashboardId) {
      loadPermissions();
    }
  }, [open, dashboardId]);

  const loadPermissions = async () => {
    setLoading(true);
    try {
      const data = await fetchDashboardPermissions(dashboardId);
      setPermissions(data);
    } catch {
      message.error("Failed to load permissions");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchUsers = async (query: string) => {
    if (query.length < 2) {
      setUserSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const data = await searchUsers(query);
      setUserSearchResults(data);
    } catch {
      setUserSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleShare = async () => {
    if (!selectedUserId) return;
    setSaving(true);
    try {
      const newPerm = await shareDashboard(dashboardId, selectedUserId, selectedPermission);
      setPermissions((prev) => [...prev, newPerm]);
      setSelectedUserId(null);
      message.success("Dashboard shared");
    } catch {
      message.error("Failed to share dashboard");
    } finally {
      setSaving(false);
    }
  };

  const handleUnshare = async (permissionId: number) => {
    try {
      await unshareDashboard(dashboardId, permissionId);
      setPermissions((prev) => prev.filter((p) => p.id !== permissionId));
      message.success("Permission removed");
    } catch {
      message.error("Failed to remove permission");
    }
  };

  const permissionTagColor = (level: DashboardPermissionLevel) => {
    switch (level) {
      case "admin": return "red";
      case "edit": return "blue";
      case "view": return "green";
    }
  };

  return (
    <Modal
      title="Share Dashboard"
      open={open}
      onCancel={onClose}
      footer={null}
      width={480}
    >
      {/* Public toggle */}
      {isOwner && (
        <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
          <div>
            <Text strong>Public access</Text>
            <br />
            <Text type="secondary" className="text-sm">
              Anyone with the link can view
            </Text>
          </div>
          <Switch
            checked={isPublic}
            onChange={(checked) => {
              onTogglePublic(checked);
              toggleDashboardPublic(dashboardId, checked).catch(() =>
                message.error("Failed to update public access")
              );
            }}
          />
        </div>
      )}

      <Spin spinning={loading}>
        {/* Existing permissions */}
        {permissions.length === 0 ? (
          <Empty description="No shared users" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <div className="space-y-2 mb-4">
            {permissions.map((perm) => (
              <div
                key={perm.id}
                className="flex items-center justify-between p-2 bg-white border rounded"
              >
                <div className="flex items-center gap-2">
                  <Tag color={permissionTagColor(perm.permission)}>
                    {perm.permission.toUpperCase()}
                  </Tag>
                  <Text>{perm.username}</Text>
                </div>
                {isOwner && (
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<CloseOutlined />}
                    onClick={() => handleUnshare(perm.id)}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Add user */}
        {isOwner && (
          <div className="border-t pt-3">
            <Text strong className="block mb-2">
              <UserAddOutlined className="mr-1" />
              Share with someone
            </Text>
            <Space direction="vertical" className="w-full">
              <Select
                className="w-full"
                showSearch
                placeholder="Search users by name or email"
                filterOption={false}
                onSearch={handleSearchUsers}
                onSelect={(val) => setSelectedUserId(val as number)}
                value={selectedUserId}
                notFoundContent={searching ? <Spin size="small" /> : <Empty description="Type to search" />}
                options={userSearchResults.map((u) => ({
                  value: u.id,
                  label: `${u.username} (${u.email})`,
                }))}
                allowClear
              />
              <Space>
                <Select
                  value={selectedPermission}
                  onChange={setSelectedPermission}
                  options={PERMISSION_OPTIONS}
                  style={{ width: 100 }}
                />
                <Button
                  type="primary"
                  onClick={handleShare}
                  disabled={!selectedUserId}
                  loading={saving}
                >
                  Share
                </Button>
              </Space>
            </Space>
          </div>
        )}
      </Spin>
    </Modal>
  );
}